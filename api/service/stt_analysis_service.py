import json


def get_wpm_analysis(stt_json):
    """
    _summary_
        STT 결과를 분석하여 WPM을 계산한다.

    Args:
        stt_json (Path): STT 결과가 저장된 json 파일 경로

    Returns:
        LPM (Letter per minute): 분당 음절 수
    """
    stt_result = json.loads(stt_json)

    letters_count = 0

    # 스크립트의 전체 음절 수 더하기
    for segment in stt_result["segments"]:
        letters_count += len(segment["text"])

    # <분당 음절 수 계산>
    # 느림: 300음절 / min
    # 보통: 350음절 / min
    # 빠름: 400음절 / min
    return letters_count / (stt_result["segments"][-1]["end"] / 1000 / 60)
