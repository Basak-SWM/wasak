import unittest

import librosa

from utils.audio import separate_audio_file, AudioSeparationMode


class TestAudioSeparation(unittest.TestCase):
    def setUp(self):
        self.original_audio_path = "./resource/test/audio/1_100.wav"

    def test_original_audio_file_length(self):
        """
        테스트용 오디오 파일의 길이는 82초
        """
        y, sr = librosa.load(self.original_audio_path, sr=None)
        sec_len = len(y) // sr
        self.assertEqual(sec_len, 82)

    def test_argument_validation_check(self):
        """
        인자가 맞게 들어왔음을 검사함
        """
        # 균등 분할하는 경우 duration이 필요
        with self.assertRaises(ValueError):
            result = separate_audio_file(
                self.original_audio_path,
                AudioSeparationMode.EQUAL,
            )

        # 여러 길이로 분할하는 경우 durations 필요
        with self.assertRaises(ValueError):
            result = separate_audio_file(
                self.original_audio_path,
                AudioSeparationMode.VARYING,
            )

    def test_equal_segments_test(self):
        """
        균등 분할 기능 테스트
        """
        duration = 10
        result = separate_audio_file(
            self.original_audio_path, AudioSeparationMode.EQUAL, duration=duration
        )
        # 82초 짜리 파일이므로 (10초씩 8개) + (2초 1개) = 9개
        self.assertEqual(len(result), 9)

    def test_varying_segments_test(self):
        """
        여러 크기로 분할 기능 테스트
        """
        durations = [10, 20, 30]
        result = separate_audio_file(
            self.original_audio_path, AudioSeparationMode.VARYING, durations=durations
        )
        # 82초 짜리 파일이므로 (10초 1개) + (20초 1개) + (30초 1개) + (나머지 22초 1개) = 4개
        self.assertEqual(len(result), 4)
