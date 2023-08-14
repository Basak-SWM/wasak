import json
from itertools import zip_longest
from api.data.enums import SpeechCorrectionType


class SpeechCorrectionBreakpointValue:
    LPM_FAST = 400
    LPM_SLOW = 300
    PAUSE_LONG = 1500
    PAUSE_SHORT = 400


def get_speech_correction(
    lpm_by_sentence: list, ptl_by_sentence: list, concatenated_script: list
):
    """
    _summary_
    속도 분석, 휴지 분석 완료 후 해당 결과를 바탕으로 교정 부호를 생성한다.

    Args:
        lpm_by_sentence: list
        ptl_by_sentence: list
        concatenated_script: list

    Returns:
        {
            'FAST': [[3, 8],[12, 15]],
            'SLOW': [[3, 8],[12, 15]],
            'PAUSE_TOO_LONG': [234,355,755],
            'PAUSE_TOO_SHORT': [234,355,755]
        }
        LPM의 경우는 문장의 범위를 나타내야 하기에 start_word_index, end_word_index를 반환.
        Pause 기호의 경우는 문장의 끝에만 교정 부호를 생성하므로 하나의 단어 인덱스만을 반환.
    """

    speech_correction_list = {
        SpeechCorrectionType.TOO_FAST.value: [],
        SpeechCorrectionType.TOO_SLOW.value: [],
        SpeechCorrectionType.PAUSE_TOO_LONG.value: [],
        SpeechCorrectionType.PAUSE_TOO_SHORT.value: [],
    }

    if not concatenated_script["segments"]:
        return speech_correction_list

    # 원본 concatenated_script에 word index 추가
    word_index = 0
    for s_idx, segment in enumerate(concatenated_script["segments"]):
        for w_idx in range(len(segment["words"])):
            concatenated_script["segments"][s_idx]["words"][w_idx] = (
                *concatenated_script["segments"][s_idx]["words"][w_idx],
                word_index,
            )
            word_index += 1

    # PTL 분석의 경우 마지막 문장 뒤에는 휴지가 없기 때문에 zip_longest를 사용한다.
    for idx, ptl in enumerate(ptl_by_sentence):
        # for idx, (lpm, ptl) in enumerate(zip_longest(lpm_by_sentence, ptl_by_sentence)):
        curr_line_start_word_idx = concatenated_script["segments"][idx]["words"][0][3]
        curr_line_end_word_idx = concatenated_script["segments"][idx]["words"][-1][3]

        # LPM 분석
        # TODO: Window 방식으로 LPM 바꿨으므로 추후 어떻게 분석 결과 넘겨줘야할지 결정해야 함.
        # if lpm >= SpeechCorrectionBreakpointValue.LPM_FAST:
        #     speech_correction_list[SpeechCorrectionType.TOO_FAST.value].append(
        #         [curr_line_start_word_idx, curr_line_end_word_idx]
        #     )
        # elif lpm < SpeechCorrectionBreakpointValue.LPM_SLOW:
        #     speech_correction_list[SpeechCorrectionType.TOO_SLOW.value].append(
        #         [curr_line_start_word_idx, curr_line_end_word_idx]
        #     )

        # PTL 분석
        if ptl and ptl >= SpeechCorrectionBreakpointValue.PAUSE_LONG:
            speech_correction_list[SpeechCorrectionType.PAUSE_TOO_LONG.value].append(
                curr_line_end_word_idx
            )
        elif ptl and ptl < SpeechCorrectionBreakpointValue.PAUSE_SHORT:
            speech_correction_list[SpeechCorrectionType.PAUSE_TOO_SHORT.value].append(
                curr_line_end_word_idx
            )

    return speech_correction_list


if __name__ == "__main__":
    with open(
        "/Users/cyh/cyh/programming/wasak/research/samples/kss_concatenated_script_sample.json",
        "r",
    ) as f1, open(
        "/Users/cyh/cyh/programming/wasak/research/samples/Analysis_LPM_sample.json",
        "r",
    ) as f2, open(
        "/Users/cyh/cyh/programming/wasak/research/samples/Analysis_PAUSE_sample.json",
        "r",
    ) as f3:
        stt = json.load(f1)
        lpm = json.load(f2)
        ptl = json.load(f3)
        print(json.dumps(get_speech_correction(lpm, ptl, stt)))
