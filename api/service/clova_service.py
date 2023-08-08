import os
import requests
from pathlib import Path

from api.configs.clova import clova_speech_config


def clova_stt_send(s3_audio_file_path: str, response_callback_url: str):
    request_body = {
        "url": s3_audio_file_path,  # 분석할 음성 파일 URL
        "language": "ko-KR",
        "callback": response_callback_url,  # 결과 송신받을 콜백 URL
    }

    headers = {"X-CLOVASPEECH-API-KEY": clova_speech_config.clova_secret_key}

    response: requests.Response = requests.post(
        clova_speech_config.clova_stt_target_url, json=request_body, headers=headers
    )

    if response.status_code == 200:
        return True
    else:
        # TODO: Error logging
        print("[DEV] Clova STT Send Failed: ", response.status_code, response.text)
        return False
