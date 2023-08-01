import json
from typing import Tuple, List


def get_average_wpm(stt_json: str) -> int:
    """
    _summary_
        STT 결과를 분석하여 WPM을 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

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


def get_lpm_by_sentense(stt_json: str) -> List[Tuple[int, int, str]]:
    """
    _summary_
        모든 segments 들을 순회하며 words 별로 걸린 시간 및 글자 수를 합산, '.'를 만나면 문장의 끝으로 판단하여 lpm_by_sentense를 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

    Returns:
        문장별 lpm 분석을 속도가 빠른 순서대로 반환.
        [
            (start_time, end_time, lpm),
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


def get_ptl_by_sentense(stt_json: str):
    """
    _summary_
        마침표 등의 기호로 문장의 끝을 판단하고 이후 이어지는 문장까지
        걸리는 시간을 휴지로 판단하여 문장별 ptl(pause time)을 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

    Returns:
    [
        (각 문장의 끝나는 시간, 이어지는 문장 직전까지의 휴지 기간 (ms)),
    ]

    """
    stt_result = json.loads(stt_json)
    end_time_before = -1
    ptl_by_sentense = []

    for segment in stt_result["segments"]:
        for start, end, word in segment["words"]:
            # 임시 저장되어있으면 문장 시작 전까지의 시간을 계산하여 휴지 기간에 더함.
            if not end_time_before == -1:
                paused_time = start - end_time_before
                ptl_by_sentense.append([end_time_before, paused_time])
                end_time_before = -1

            # 문장이 끝나면 바로 뒤에 문장 시작 전까지의 시간 계산 위해 끝나는 시간 임시 저장
            if "." in word or "?" in word or "!" in word:
                end_time_before = end

    return ptl_by_sentense


def get_average_ptl_VER1(stt_json: str):
    """
    _summary_
        말을 하고 있지 않은 시간이 전체 대본 스크립트에서
        몇 퍼센트를 차지하는지 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

    Returns:

    """
    stt_result = json.loads(stt_json)

    # 시간 단위는 millisecond
    elapsed_time = 0
    total_time = stt_result["segments"][-1]["end"]

    for segment in stt_result["segments"]:
        for word in segment["words"]:
            elapsed_time += word[1] - word[0]

    average_ptl = (1 - (elapsed_time / total_time)) * 100

    return average_ptl


def get_average_ptl_VER2(stt_json: str):
    """
    _summary_
        문장 별 사이 시간만 휴지로 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

    Returns:

    """
    stt_result = json.loads(stt_json)
    end_time_before = -1

    # 시간 단위는 millisecond
    paused_time = 0
    total_time = stt_result["segments"][-1]["end"]

    for segment in stt_result["segments"]:
        for start, end, word in segment["words"]:
            # 임시 저장되어있으면 문장 시작 전까지의 시간을 계산하여 휴지 기간에 더함.
            if not end_time_before == -1:
                paused_time += start - end_time_before
                end_time_before = -1

            # 문장이 끝나면 바로 뒤에 문장 시작 전까지의 시간 계산 위해 끝나는 시간 임시 저장
            if "." in word or "?" in word or "!" in word:
                end_time_before = end

    average_ptl = (paused_time / total_time) * 100

    return average_ptl


if __name__ == "__main__":
    with open(
        "/Users/cyh/Downloads/basak-test_y2mate.com - 서양에선 왜 비가와도 우산을 쓰지 않을까 우산 속에 숨겨진 마초 문화.mp3_2023-07-04-202627147 (2).json",
        "r",
    ) as f:
        stt_json = f.read()

    print(get_ptl_by_sentense(stt_json))
