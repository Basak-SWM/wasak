from pathlib import Path
import noisereduce as nr
from scipy.io import wavfile
from cache_service import get_cache_file_path


def remove_noise_from_wav_record(wav_file_to_process_path: Path) -> str:
    """_summary_
    목소리 제외 wav파일의 노이즈를 제거한다.

    Args:
        webm_files_path_list (List[str]): Segment webm 파일들의 경로를 담은 list

    Returns:
        Path: 생성된 wav 파일 경로 (S3 업로드 후 해당 파일 삭제해야 함.)
    """
    rate, data = wavfile.read(wav_file_to_process_path)
    reduced_noise = nr.reduce_noise(y=data, sr=rate, stationary=True)
    processed_wav_file_path = get_cache_file_path("wav")
    wavfile.write(str(processed_wav_file_path), rate, reduced_noise)
    return processed_wav_file_path
