from functools import reduce
from typing import Any, List, Tuple
from copy import deepcopy

import kss


class AlignedSttElement:
    def __init__(self, full_text: str) -> None:
        # words로 구성된 원본 텍스트
        self.full_text = full_text[:]
        # List[(int, int, str)] 형태로 구성된 단어들 (각각 시작 millisecond, 끝 millisecond, 단어)
        self.words = []
        # 해당 문장이 STT 결과와 KSS 결과가 달라 깨져 있는지 여부
        self.broken = False

    def deserialize(self):
        return {
            "full_text": self.full_text,
            "words": self.words,
        }


class SpeechService:
    def get_concatenated_stt_script(self, stt_script: dict) -> Any:
        segments = stt_script["segments"]

        concatenated_segment = {
            "start": segments[0]["start"],
            "end": segments[-1]["end"],
            "text": " ".join(map(lambda s: s["text"], segments)),
            "confidence": sum(map(lambda s: s["confidence"], segments)) / len(segments),
            "words": reduce(lambda acc, cur: acc + cur["words"], segments, []),
            "textEdited": " ".join(map(lambda s: s["textEdited"], segments)),
            "diarization": {"label": ""},  # 화자 인식은 꺼져 있는 것으로 가정
            "speaker": {
                "label": "",
                "name": "",
                "edited": False,
            },  # 화자 인식은 꺼져 있는 것으로 가정
        }

        ret = deepcopy(stt_script)
        ret["segments"] = [concatenated_segment]

        return ret

    def _do_alignment(
        self, words: Tuple[int, int, str], splitted_sentences: List[str]
    ) -> List[AlignedSttElement]:
        # 처리할 단어의 인덱스 (Queue의 역할을 수행하며, 증가하기만 한다.)
        c_idx = 0

        # 문장 앞뒤로 남아 있을 수 있는 whitespace를 전처리
        splitted_sentences = list(map(str.strip, splitted_sentences))

        # 스피치를 구성하는 단어를 앞에서부터 하나씩 빼서 문장을 재구성한다.
        # 이때 KSS와 STT 결과가 서로 단어를 다른 단위로 인식한다면(예: KSS는 '안녕하세요'를 하나의 단어로 인식하고, STT는 '안녕'과 '하세요'로 인식한다면)
        # STT의 결과를 우선적으로 사용한다.
        # 재조합된 문장들을 담을 리스트 (element는 아래 `current`를 참고)
        reconstructed_sentences = []
        for s_idx, sentence in enumerate(splitted_sentences):
            current = AlignedSttElement(sentence)

            # 원본 문자열을 수정하지 않도록 하기 위해 사용
            processing_sentence = sentence[:]

            # 종료 조건: 문장이 빈 문자열이 되면 종료
            while True:
                processing_sentence = processing_sentence.lstrip()
                # 단 문장의 맨 앞에 현재 처리해야 할 단어가 있는지 확인하므로, 앞에 포함된 공백을 삭제함
                if not processing_sentence:
                    break

                # 현재 처리해야 할 단어에 대해,
                start, end, word = words[c_idx]
                # 현재 처리할 단어로 현재 처리할 문장이 시작된다면
                if processing_sentence.startswith(word):
                    # 해당 문장을 구성하는 단어로 추가하고
                    current.words.append((start, end, word))
                    # 해당 단어 부분만큼 삭제해줌
                    processing_sentence = processing_sentence[len(word) :]
                    # 다음 단어를 처리하기 위해 인덱스를 증가시킴
                    c_idx += 1
                # 처리해야 할 문자가 남았으나 word로 시작되지 않는 경우, STT 결과와 KSS 결과가 다른 깨진 문장임
                else:
                    # 깨져 있는 문장의 앞 부분을 삭제하고 (`안녕` + `하세요` 중 `안녕`만 현 문장에 포함된 것이므로, `안녕`을 뒤의 문장으로 붙여주는 것)
                    current.full_text = current.full_text[: -len(word)]
                    # 남은 부분을 다음 문장의 앞에 붙여줌
                    splitted_sentences[s_idx + 1] = (
                        processing_sentence + splitted_sentences[s_idx + 1]
                    )
                    # 현재 문장이 깨져 있음을 표시하고, 다음 문장으로 넘어감 (word는 아직 처리되지 않았으므로 c_idx는 그대로)
                    current.broken = True
                    break

            reconstructed_sentences.append(current)

            reconstructed_sentences = list(
                map(lambda x: x.deserialize(), reconstructed_sentences)
            )

            return reconstructed_sentences