from pathlib import Path
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""
서비스에서 사용할 음성 분석 모듈
"""


def get_f0_analysis(audio_file_path: Path):
    """
    _summary_
        음성 파일의 pitch track을 분석한다.

    Args:
        audio_file_path (Path): 분석할 음성 파일 경로

    Returns:
        Dict: pitch track 분석 결과
            {
                "times": [0.0, 0.01, ...],
                "f0_smoothed": [0.0, 0.01, ...]
            }
    """
    # Load the wav file with librosa
    audio_data, sample_rate = librosa.load(audio_file_path)

    # Use pYIN to estimate the fundamental frequency (pitch track)
    f0, voiced_flag, voiced_probs = librosa.pyin(audio_data, fmin=85, fmax=255)

    # Convert unvoiced segments to NaN
    f0 = np.where(voiced_flag, f0, np.nan)

    # Interpolate to fill NaNs
    valid = np.isfinite(f0)
    x = np.arange(len(f0))

    # Interpolation for the valid indices
    # f0_interpolated = np.interp(x, x[valid], f0[valid])
    f0_interpolated = f0

    # Calculate moving average with a window size of 50
    # f0_smoothed = pd.Series(f0_interpolated).rolling(window=12, min_periods=1, center=True).mean()
    f0_smoothed = (
        pd.Series(f0_interpolated).rolling(window=50, min_periods=1, center=True).mean()
    )
    # f0_smoothed = f0

    times = librosa.times_like(f0)

    # [DEV]
    # Plot the smoothed pitch track
    # plt.figure(figsize=(12, 6))
    # plt.plot(times, f0_smoothed, label="f0", color="red")
    # plt.legend(loc="upper right")
    # plt.xlabel("Time (s)")
    # plt.ylabel("Frequency (Hz)")
    # plt.title("Pitch track")
    # plt.grid()
    # plt.show()

    # FIXME: noisereduce 하면 너무 소리가 띄엄띄엄되고, 안하면 들쭉날쭉함
    return {"times": times.tolist(), "f0_smoothed": f0_smoothed.tolist()}


def get_f0_average(audio_file_path: Path) -> str:
    """
    _summary_
        단일 스피치의 평균 f0을 반환.

    Args:
        audio_file_path (Path): 분석할 음성 파일 경로

    Returns:
        str: 평균 f0 값 반환 / ex) 남자 목소리: 120, 여자 목소리: 220
    """
    audio_data, sample_rate = librosa.load(audio_file_path)

    # Use pYIN to estimate the fundamental frequency (pitch track)
    f0, voiced_flag, voiced_probs = librosa.pyin(audio_data, fmin=85, fmax=300)

    # Filter out unvoiced segments
    f0_voiced = f0[voiced_flag]

    # Calculate and print the average f0
    average_f0 = np.nanmean(f0_voiced)

    return average_f0


def get_db_analysis(audio_file_path: Path):
    """
    _summary_
        음성 파일의 db를 분석한다.

    Args:
        audio_file_path (Path): 분석할 음성 파일 경로

    Returns:
        Dict: voice db 분석 결과
            {
                "times": [0.0, 0.01, ...],
                "loudness": [0.0, 0.01, ...]
            }
    """
    # Load the audio file
    y, sr = librosa.load(audio_file_path)

    # Calculate the STFT of the signal
    stft = librosa.stft(y)

    # Convert to dB
    stft_db = librosa.amplitude_to_db(abs(stft))

    # Average over frequencies for each time point
    loudness = np.mean(stft_db, axis=0)

    # Shift dB values so that smallest value is 0
    loudness -= np.min(loudness)

    # Create an array of time points
    time = librosa.frames_to_time(range(loudness.shape[0]), sr=sr)

    return {"times": time.tolist(), "loudness": loudness.tolist()}

    # [DEV]
    # Plot the results
    # plt.figure(figsize=(10, 6))
    # plt.plot(time, loudness)
    # plt.xlabel('Time (s)')
    # plt.ylabel('Loudness (dB, relative)')
    # plt.title('Loudness over Time')
    # plt.show()