import json
from typing import List


def get_wpm_analysis(stt_json) -> int:
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


def get_lpm_by_sentense(stt_json) -> List[List[int, int, str]]:
    """
    _summary_
        모든 segments 들을 순회하며 words 별로 걸린 시간 및 글자 수를 합산, '.'를 만나면 문장의 끝으로 판단하여 lpm_by_sentense를 계산한다.

    Args:
        stt_json (Path): STT 결과가 저장된 json 파일 경로

    Returns:
        문장별 lpm 분석을 속도가 빠른 순서대로 반환.
        [
            [start_time, end_time, lpm],
        ]

    """
    stt_result = json.loads(stt_json)

    lpm_by_sentense = []

    letters_count = 0
    start_time = -1

    for segment in stt_result["segments"]:
        for start, end, word in segment["words"]:
            start_time = start if start_time == -1 else start_time
            letters_count += len(word)
            # TODO: 기호로 문장의 끝을 판단했으나 다른 기호도 존재하는지 확인 필요
            if "." in word or "?" in word or "!" in word:
                letters_count -= 1
                lpm = letters_count / ((end - start_time) / 1000 / 60)
                lpm_by_sentense.append([start_time, end, lpm])
                letters_count = 0
                start_time = -1

    # lpm 순서대로 정렬
    lpm_by_sentense.sort(key=lambda x: x[2], reverse=True)

    return lpm_by_sentense
