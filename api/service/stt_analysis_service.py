from collections import Counter
import json
from typing import Tuple, List


def get_average_lpm(stt_json: dict) -> int:
    """
    _summary_
        STT 결과를 분석하여 LPM (Letters per minute)을 계산한다.

    Args:
        stt_json (str): Clova에서 받은 STT 결과

    Returns:
        LPM (Letters per minute): 분당 음절 수
    """
    # FIXME: 평균 LPM이 문장별 LPM의 평균을 의미하는지, 전체 음성의 LPM을 의미하는지 결정 필요
    only_letters_text = stt_json["text"].replace(" ", "").replace(".", "")

    # <분당 음절 수 계산>
    # 느림: 300음절 / min
    # 보통: 350음절 / min
    # 빠름: 400음절 / min
    if not stt_json["segments"]:
        return 0.0
    return len(only_letters_text) / (stt_json["segments"][-1]["end"] / 1000 / 60)


def get_lpm_by_sentence(stt_json: dict) -> List[Tuple[int, int, str]]:
    """
    _summary_
        모든 segments 들을 순회하며 words 별로 걸린 시간 및 글자 수를 합산, '.'를 만나면 문장의 끝으로 판단하여 lpm_by_sentence를 계산한다.

    Args:
        stt_json (dict): Clova에서 받은 STT 결과를 reconstruct한 json

    Returns:
        List[int]: 문장별 lpm 분석 결과를 기존 index에 맞춰 반환
    """

    lpm_by_sentence = [
        len(s["text"].replace(" ", "").replace(".", ""))
        / (s["end"] - s["start"])
        * 1000
        * 60
        for s in stt_json["segments"]
    ]

    return lpm_by_sentence


def get_lpm_heatmap(stt_json: dict) -> List[int]:
    """
    _summary_

    Args:
        stt_json (dict): Clova에서 받은 STT 결과를 reconstruct한 json

    Returns:
        List[int]: 단어별 속도를 -10 ~ +10으로 분석
    """
    # FIXME: 앞 뒤로 공평하게 선택되도록 초반과 후반의 item들에게 중복 window 적용 필요
    WINDOW_SIZE_CONSTANT = 10

    def get_lpm(start_time: int, end_time: int, letter_count: int):
        return letter_count / (end_time - start_time) * 1000 * 60

    words = []

    # 모든 단어에 word_index를 붙여서 unpack
    word_index = 0
    for s_idx, segment in enumerate(stt_json["segments"]):
        for w_idx in range(len(segment["words"])):
            words.append(
                (
                    *stt_json["segments"][s_idx]["words"][w_idx],
                    word_index,
                )
            )
            word_index += 1

    word_speed = [0] * len(words)

    # Window Size 보다 word length가 짧으면 에러나서 수정
    WINDOW_SIZE = min(WINDOW_SIZE_CONSTANT, len(words))

    # 앞에서 잘리는 부분 따로 window 선택해줌
    for idx in range(WINDOW_SIZE - 1):
        start_time = words[0][0]
        end_time = words[idx + 1][1]
        letter_count = sum([len(w[2]) for w in words[: idx + 1]])

        lpm = get_lpm(start_time, end_time, letter_count)
        if lpm > 400:
            word_speed[: idx + 1] = [x + 1 for x in word_speed[: idx + 1]]
        elif lpm < 300:
            word_speed[: idx + 1] = [x - 1 for x in word_speed[: idx + 1]]

    # 앞 뒤 제외 동일한 비중으로 선택되는 window 선택지
    for idx in range(len(words) - WINDOW_SIZE):
        start_time = words[idx][0]
        end_time = words[idx + WINDOW_SIZE - 1][1]
        letter_count = sum([len(w[2]) for w in words[idx : idx + WINDOW_SIZE]])

        lpm = get_lpm(start_time, end_time, letter_count)
        if lpm > 400:
            word_speed[idx : idx + WINDOW_SIZE] = [
                x + 1 for x in word_speed[idx : idx + WINDOW_SIZE]
            ]
        elif lpm < 300:
            word_speed[idx : idx + WINDOW_SIZE] = [
                x - 1 for x in word_speed[idx : idx + WINDOW_SIZE]
            ]

    # 뒤에서 잘리는 부분 따로 window 선택해줌
    for idx in range(len(words) - WINDOW_SIZE, len(words)):
        start_time = words[idx][0]
        end_time = words[-1][1]
        letter_count = sum([len(w[2]) for w in words[idx:]])

        lpm = get_lpm(start_time, end_time, letter_count)
        if lpm > 400:
            word_speed[idx:] = [x + 1 for x in word_speed[idx:]]
        elif lpm < 300:
            word_speed[idx:] = [x - 1 for x in word_speed[idx:]]

    result = {"WINDOW_SIZE": WINDOW_SIZE, "speed_list": word_speed}
    return result


def get_ptl_by_sentence(stt_json: dict):
    """
    _summary_
        마침표 등의 기호로 문장의 끝을 판단하고 이후 이어지는 문장까지
        걸리는 시간을 휴지로 판단하여 문장별 ptl(pause time)을 계산한다.

    Args:
        stt_json (dict): Clova에서 받은 STT 결과를 reconstruct한 json

    Returns:
    List:
        이어지는 문장 직전까지의 휴지 기간 (ms)
        (즉, 본 list의 length는 segments의 length - 1)
    """
    ptl_by_sentence = [
        stt_json["segments"][idx + 1]["start"] - sentence["end"]
        for idx, sentence in enumerate(stt_json["segments"])
        if idx + 1 != len(stt_json["segments"])
    ]
    return ptl_by_sentence


def get_ptl_ratio(stt_json: dict):
    """
    _summary_
        ptl (pause time length) 계산 함수
        단어 간 사이 공백 시간들 중 100ms를 넘어가는 것만 휴지로 판단하여 합산.

    Args:
        stt_json (dict): Clova에서 받은 STT 결과

    Returns:
        float: 전체 휴지 시간 / 전체 시간 * 100

    """
    paused_time = 0
    end_time_before = -1

    for segment in stt_json["segments"]:
        for idx, (start, end, word) in enumerate(segment["words"]):
            paused_time_candidate = 0
            # 현재 segment의 끝이면 다음 segment의 첫 단어까지의 시간 계산
            if end_time_before != -1:
                paused_time_candidate = start - end_time_before
                end_time_before = -1
            if idx + 1 == len(segment["words"]):
                end_time_before = end
            else:
                paused_time_candidate = segment["words"][idx + 1][0] - end
            if paused_time_candidate >= 100 or True:
                paused_time += paused_time_candidate

    if not stt_json["segments"]:
        return 100.0
    else:
        return paused_time / stt_json["segments"][-1]["end"] * 100


# TEST
if __name__ == "__main__":
    with open(
        "/Users/cyh/cyh/programming/wasak/research/samples/지식브런치_stt.json",
        "r",
    ) as f:
        concatenated_script = json.loads(f.read())
        a = get_lpm_heatmap(concatenated_script)
        print(a)
