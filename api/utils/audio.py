from typing import Tuple, List, Optional
import os
from enum import Enum
import math

import librosa
import soundfile as sf
import numpy as np


class AudioSeparationMode(Enum):
    """
    일정 간격으로 오디오 데이터를 자르는 방법을 의미함
    """

    # 균등 분할
    EQUAL = "EQUAL"
    # 여러 값들로 분할
    VARYING = "VARYING"


class AudioLengthExceededException(ValueError):
    """
    요청된 음성 파일에 대한 특정 시점이 처리 대상 오디오의 길이를 넘는 경우 발생
    """


def separate_audio_file(
    audio_path: str,
    mode: AudioSeparationMode,
    duration: Optional[int] = None,
    durations: Optional[List[int]] = None,
) -> List[Tuple[int, np.ndarray]]:
    """
    오디오 파일을 특정 간격으로 분할하여 반환하는 함수

    :param audio_path: 읽어들일 원본 오디오 파일의 경로
    :param mode: 분할 모드
    :param duration: 균등 분할 구간 길이(초) (AudioSeparationMode.EQUAL인 경우 required)
    :param durations: 분할 구간 길이의 목록(초) (AudioSeparationMode.VARYING인 경우 required)
    :returns: (sample rate, 1차원 오디오 데이터 배열)
        단, AudioSeparationMode.EQUAL이며 duration이 원본 오디오 파일의 길이를 넘는 경우 duration만큼 샘플링 되며, duration보다 작은
        나머지 부분은 결과의 맨 뒤에 저장된다.
        AudioSeparationMode.VARYING이며 durations의 합이 원본 오디오 파일의 길이를 넘는 경우 AudioLengthExceededException 발생하고,
        그보다 부족한 경우 나머지 부분은 결과의 맨 뒤에 저장된다.
    :raises ValueError: mode별로 요구되는 argument들이 전달되지 않은 경우
    :raises AudioLengthExceededException:
        AudioSeparationMode.VARYING이며, durations의 합이 원본 오디오 파일의 길이를 넘기는 경우
    """
    ret: List[Tuple[int, np.ndarray]] = []

    y, sr = librosa.load(audio_path, sr=None)

    # duration 길이로 균등 분할 모드
    if mode == AudioSeparationMode.EQUAL:
        if duration is None:
            raise ValueError(
                f"Argument 'duration' is required with mode={AudioSeparationMode.EQUAL}"
            )

        sample_duration = math.floor(duration * sr)  # 샘플링 수

        # 샘플링 수를 기준으로 WAV 파일 끊기
        num_segments = math.ceil(len(y) / sample_duration)
        for i in range(num_segments):
            start = i * sample_duration
            end = min((i + 1) * sample_duration, len(y))
            segment = y[start:end]
            ret.append((sr, segment))

    # durations에 저장된 길이들로 우선 분할하고, 남는 경우 ret의 맨 마지막 요소로 추가
    elif mode == AudioSeparationMode.VARYING:
        if durations is None:
            raise ValueError(
                f"Argument 'durations' is required with mode={AudioSeparationMode.VARYING}"
            )

        total_duration = sum(durations)
        if total_duration > len(y):
            raise AudioLengthExceededException(
                "The sum of durations is longer than the audio file."
            )

        start = 0
        for i, dur in enumerate(durations):
            end = start + math.floor(dur * sr)
            segment = y[start:end]
            start = end
            ret.append((sr, segment))

        # 남은 경우 맨 끝 구간 추가
        audio_length_sec = len(y) / sr
        if audio_length_sec - total_duration > 0:
            start = end
            end = math.floor(audio_length_sec * sr)
            segment = y[start:end]
            ret.append((sr, segment))

    return ret


def save_segment_as_file(segment: np.ndarray, sr: int, file_path: str) -> None:
    """
    segment와 sample rate를 인자로 받아 file_path에 오디오 파일로 저장하는 함수
    :func: 'separate_audio_file'의 반환 값을 참고하여 사용
    """
    sf.write(file_path, segment, sr)


if __name__ == "__main__":
    # 82초 길이의 샘플
    audio_path = "./resource/test/audio/1_100.wav"

    # 균등 분할 테스트
    duration = 10
    separation_result = separate_audio_file(
        audio_path, AudioSeparationMode.EQUAL, duration=duration
    )
    # for i, (sample_rate, segment) in enumerate(separation_result):
    #     path = os.path.join(
    #         "./resource/test/audio", "EQUAL_SEPARATION", f"segment_{i+1}.wav"
    #     )
    #     save_segment_as_file(segment, sample_rate, path)

    # 여러 길이로 분할 테스트
    durations = [10, 20, 30]
    separation_result = separate_audio_file(
        audio_path, AudioSeparationMode.VARYING, durations=durations
    )
    # for i, (sample_rate, segment) in enumerate(separation_result):
    #     path = os.path.join(
    #         "./resource/test/audio", "VARYING_SEPARATION", f"segment_{i+1}.wav"
    #     )
    #     save_segment_as_file(segment, sample_rate, path)
