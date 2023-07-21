import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""
서비스에서 사용할 음성 분석 모듈
"""


def get_f0_analysis(audio_file_path: str):
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

    # Plot the smoothed pitch track
    times = librosa.times_like(f0)
    plt.figure(figsize=(12, 6))
    plt.plot(times, f0_smoothed, label="f0", color="red")
    plt.legend(loc="upper right")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title("Pitch track")
    plt.grid()
    plt.show()

    # FIXME: noisereduce 하면 너무 소리가 띄엄띄엄되고, 안하면 들쭉날쭉함
    return {"times": times.tolist(), "f0_smoothed": f0_smoothed.tolist()}
