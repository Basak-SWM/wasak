from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Analysis1(BaseModel):
    callback_url: str
    upload_url: str
    download_url: str


@app.post("/{speech_id}/analysis-1")
def trigger_analysis_1(dto: Analysis1):
    print(dto)
    return None


@app.post("/{speech_id}/analysis-2")
def trigger_analysis_2():
    return None
