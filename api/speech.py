from fastapi import FastAPI
from pydantic import BaseModel
import concurrent.futures


app = FastAPI()


class Analysis1(BaseModel):
    '''
    ## 클로바로 넘겨줄 값
    callback_url : stt 결과를 전송할 dalcom endpoint
    download_url : stt 입력 파일이 저장된 object의 presigned url
    ## wasak에서 쓸 값
    upload_url : wasak에서 합친 오디오 파일(full audio)을 업로드할 presigned url @
    '''
    callback_url: str
    upload_url: str
    download_url: str


@app.post("/{speech_id}/analysis-1")
def trigger_analysis_1(dto: Analysis1):
    concurrent
    print(dto)
    return None


@app.post("/{speech_id}/analysis-2")
def trigger_analysis_2():
    return None
