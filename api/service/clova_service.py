import os
import requests
from pathlib import Path


def clova_stt_send(audio_file_path: Path, response_callback_url: str):
    request_body = {
        "url": audio_file_path,  # 분석할 음성 파일 URL
        "language": "ko-KR",
        "callback": response_callback_url,  # 결과 송신받을 콜백 URL
    }

    headers = {"X-CLOVASPEECH-API-KEY": os.getenv("CLOVA_SECRET_KEY")}

    response = requests.post(
        os.getenv("CLOVA_STT_TARGET_URL"), json=request_body, headers=headers
    )

    if response.status_code == 200:
        return True
    else:
        return False
