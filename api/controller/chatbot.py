import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.data.enums import AIChatLogRole, AIChatLogStatus
from api.data.tables import AIChatLog, Speech, Presentation
from api.data.client import (
    AIChatLogDatabaseClient,
    SpeechDatabaseClient,
    PresentationDatabaseClient,
)

from api.configs.open_ai import open_ai_config
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate

from api.service.aws.s3 import S3Service

app = FastAPI()

presentation_db_client = PresentationDatabaseClient()
speech_db_client = SpeechDatabaseClient()
ai_chat_logs_db_client = AIChatLogDatabaseClient()


s3_service = S3Service()

init_prompts = [
    "너는 지금부터 스피치 스크립트를 평가하고, 개선할 수 있도록 도와주는 AI 코치야",
    "스피치 스크립트 작성을 위한 답변 외에는 대답해서는 안되고, 반드시 한국어로 응답해줘",
    "스크립트는 다음과 같아: {script}",
    "이 사용자가 잘 하고 싶은 부분은 다음과 같아: {checkpoint}",
    "이 사용자가 의도한 스피치의 개요는 다음과 같아: {outline}",
    "모든 응답은 200자 이내로 해줘",
]


def get_logs_of(speech_id):
    return ai_chat_logs_db_client.conditional_select_all(
        [AIChatLog.speech_id.bool_op("=")(speech_id)]
    )


def is_initialized(speech_id):
    return (
        len(
            list(
                filter(lambda l: l.role == AIChatLogRole.SYSTEM, get_logs_of(speech_id))
            )
        )
        > 0
    )


@app.get("/{speech_id}")
def get_ai_chat_logs(speech_id: int):
    logs = get_logs_of(speech_id)
    public_logs = list(
        filter(lambda l: l.role in (AIChatLogRole.AI, AIChatLogRole.HUMAN), logs)
    )

    for log in public_logs:
        if log.status == AIChatLogStatus.ERROR:
            log.content = f"(에러가 발생했습니다. 원문 : {log.content})"

    return public_logs


@app.post("/{speech_id}/initialize")
def init_ai_chat_logs(speech_id: int):
    speech = speech_db_client.get_single([Speech.id.bool_op("=")(speech_id)])
    if not speech:
        raise HTTPException(status_code=404)

    if is_initialized(speech_id):
        raise HTTPException(status_code=409, detail="Already initialized")
    else:
        presentation = presentation_db_client.get_single(
            [Presentation.id.bool_op("=")(speech.presentation_id)]
        )

        script_key = f"{presentation.id}/{speech.id}/analysis/STT.json"
        script = json.loads(s3_service.download_json_object(script_key))["text"]
        checkpoint = (
            "(없음)" if presentation.checkpoint is None else presentation.checkpoint
        )
        outline = "(없음)" if presentation.outline is None else presentation.outline
        template_input = {
            "script": script,
            "checkpoint": checkpoint,
            "outline": outline,
        }

        for prompt in init_prompts:
            vo = AIChatLog()
            vo.speech_id = speech_id
            vo.role = AIChatLogRole.SYSTEM
            vo.status = AIChatLogStatus.DONE
            vo.content = prompt.format(**template_input)
            ai_chat_logs_db_client.insert(vo)

        user_init_prompt = AIChatLog()
        user_init_prompt.speech_id = speech_id
        user_init_prompt.role = AIChatLogRole.HUMAN
        user_init_prompt.status = AIChatLogStatus.WAIT
        user_init_prompt.content = "스피치 스크립트에 대한 평가를 해주세요."
        ai_chat_logs_db_client.insert(user_init_prompt)

        # 초기 질의
        logs = get_logs_of(speech.id)
        messages = [(log.role.value, log.content) for log in logs]
        llm = ChatOpenAI(
            temperature=0.0, openai_api_key=open_ai_config.open_ai_secret_key
        )
        chain = ChatPromptTemplate.from_messages(messages) | llm

        try:
            result = chain.invoke({})
        except Exception:
            # 응답 실패 저장
            user_init_prompt.status = AIChatLogStatus.ERROR
            ai_chat_logs_db_client.update(user_init_prompt)
        else:
            # 요청 성공 저장
            user_init_prompt.status = AIChatLogStatus.DONE
            ai_chat_logs_db_client.update(user_init_prompt)

            # 응답 저장
            answer_init_prompt = AIChatLog()
            answer_init_prompt.speech_id = speech_id
            answer_init_prompt.role = AIChatLogRole.AI
            answer_init_prompt.status = AIChatLogStatus.DONE
            answer_init_prompt.content = result.content
            ai_chat_logs_db_client.insert(answer_init_prompt)


class SinglePromptModel(BaseModel):
    prompt: str


@app.post("/{speech_id}")
def post_ai_chat_logs(speech_id: int, dto: SinglePromptModel):
    if not is_initialized(speech_id):
        raise HTTPException(status_code=400)

    speech = speech_db_client.get_single([Speech.id.bool_op("=")(speech_id)])
    if not is_initialized(speech.id):
        raise HTTPException(status_code=409, detail="Not initialized")

    if not dto.prompt:
        raise HTTPException(status_code=400, detail="Empty prompt")

    prompt = AIChatLog()
    prompt.speech_id = speech.id
    prompt.role = AIChatLogRole.HUMAN
    prompt.status = AIChatLogStatus.WAIT
    prompt.content = dto.prompt
    ai_chat_logs_db_client.insert(prompt)

    logs = get_logs_of(speech.id)
    messages = [(log.role.value, log.content) for log in logs]
    llm = ChatOpenAI(temperature=0.0, openai_api_key=open_ai_config.open_ai_secret_key)
    chain = ChatPromptTemplate.from_messages(messages) | llm

    print(logs)

    try:
        result = chain.invoke({})
    except Exception as e:
        # 응답 실패 저장
        prompt.status = AIChatLogStatus.ERROR
        ai_chat_logs_db_client.update(prompt)
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error occurred")
    else:
        # 요청 성공 저장
        prompt.status = AIChatLogStatus.DONE
        ai_chat_logs_db_client.update(prompt)

        # 응답 저장
        answer = AIChatLog()
        answer.speech_id = speech_id
        answer.role = AIChatLogRole.AI
        answer.status = AIChatLogStatus.DONE
        answer.content = result.content
        ai_chat_logs_db_client.insert(answer)

    latest_2_logs = ai_chat_logs_db_client.select_all()[-2:]
    question, answer = latest_2_logs
    return {"question": question, "answer": answer}
