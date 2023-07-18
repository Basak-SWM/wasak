from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


class ClovaSttSendModel(BaseModel):
    data_url: str
    response_callback_url: str


@app.post("/send-analysis")
async def clova_stt_send(dto: ClovaSttSendModel):
    url = os.getenv("CLOVA_STT_TARGET_URL") + "/recognizer/url"

    data = {
        "url": dto.data_url,  # 분석할 음성 파일 URL
        "language": "ko-KR",
        "callback": dto.response_callback_url,  # 결과 송신받을 콜백 URL
    }

    headers = {"X-CLOVASPEECH-API-KEY": os.getenv("CLOVA_SECRET_KEY")}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return {"result": response.text}
    elif response.status_code == 400:
        return {"error": "Bad request"}
    else:
        return {"error": "Unexpected error"}
