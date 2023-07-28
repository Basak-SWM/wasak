import ffmpeg
from pathlib import Path
from typing import List
from api.service.cache_service import get_cache_file_path
from api.utils.bytes import concat_files

"""
*주의* ffmpeg가 OS의 PATH에 등록되어 있어야 함.
"""


def merge_webm_files_to_wav(webm_files_path_list: List[str]) -> str:
    """_summary_
    여러 webm 파일을 하나의 wav 파일로 병합한다.

    Args:
        webm_files_path_list (List[str]): Segment webm 파일들의 경로를 담은 list

    Raises:
        FileNotFoundError: 제공된 Segment webm 파일 경로가 올바르지 않을 경우

    Returns:
        Path: 생성된 wav 파일 경로 (S3 업로드 후 해당 파일 삭제해야 함.)
    """

    # 1. 병합 대상 webm 파일들을 단순 binary concat 통해서 이어붙임.
    merged_webm_binary = concat_files(webm_files_path_list)
    merged_webm_file_path = get_cache_file_path("webm")
    with open(merged_webm_file_path, "wb") as f:
        f.write(merged_webm_binary)

    # 2. ffmpeg 이용해서 webm 파일 wav 변환
    output_wav_path = get_cache_file_path("wav")
    (
        ffmpeg.input(str(merged_webm_file_path))
        .output(str(output_wav_path))
        .global_args("-loglevel", "error")
        .run()
    )

    # 3. 변환 후 병합된 원본 webm 파일 삭제
    merged_webm_file_path.unlink()

    return output_wav_path


def wav_to_mp3(wav_file_path: Path) -> Path:
    """_summary_
    wav 파일을 mp3 파일로 변환한다.

    Args:
        wav_file_path (Path): wav 파일 경로

    Returns:
        Path: mp3 파일 경로
    """

    output_mp3_path = get_cache_file_path("mp3")
    (
        ffmpeg.input(str(wav_file_path))
        .output(str(output_mp3_path), ar=22050, ab="64k")
        .global_args("-loglevel", "error")
        .run()
    )

    return output_mp3_path
