import os
import requests
from pathlib import Path

from api.configs.clova import clova_speech_config


def clova_stt_send(audio_file_path: Path, response_callback_url: str):
    request_body = {
        "url": str(audio_file_path),  # 분석할 음성 파일 URL
        "language": "ko-KR",
        "callback": response_callback_url,  # 결과 송신받을 콜백 URL
        "resultToObs": True,
    }

    headers = {"X-CLOVASPEECH-API-KEY": clova_speech_config.clova_secret_key}

    print(
        "clova_speech_config.clova_stt_target_url:",
        clova_speech_config.clova_stt_target_url,
    )
    print("request_body:", request_body)
    response: requests.Response = requests.post(
        clova_speech_config.clova_stt_target_url, json=request_body, headers=headers
    )

    if response.status_code == 200:
        print(response.json())
        return True
    else:
        return False
