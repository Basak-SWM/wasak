import ffmpeg
import uuid
import datetime
import os
from pathlib import Path
from typing import List

"""
*주의* ffmpeg가 OS의 PATH에 등록되어 있어야 함.
"""

# 임시 저장 경로 저장
CACHE_DIR_PATH = Path("cache").resolve()
CACHE_DIR_PATH.mkdir(parents=True, exist_ok=True)


def get_temp_file_name(suffix: str):
    return f'{datetime.datetime.now().strftime("%Y%m%d%H%M")}_{uuid.uuid4()}.{suffix}'


def merge_webm_files_to_mp3(webm_files_path_list: List[str]) -> str:
    """_summary_
    여러 webm 파일을 하나의 mp3 파일로 병합한다.

    Args:
        webm_files_path_list (List[str]): Segment webm 파일들의 경로를 담은 list

    Raises:
        FileNotFoundError: 제공된 Segment webm 파일 경로가 올바르지 않을 경우

    Returns:
        Path: 생성된 mp3 파일 경로 (S3 업로드 후 해당 파일 삭제해야 함.)
    """

    # 1. 병합 대상 webm 파일들의 절대 경로들을 txt 파일에 기록한다.
    webm_list_text_file_path = CACHE_DIR_PATH / get_temp_file_name("txt")

    with open(webm_list_text_file_path, "w") as f:
        for item in webm_files_path_list:
            if (target_path := Path(item)).is_file():
                f.write(f"file '{target_path}'\n")
            else:
                raise FileNotFoundError(
                    f"Audio Segment File {target_path} is not found."
                )

    # 2. ffmpeg로 음성 파일 목록 txt 파일 읽어서 하나의 webm 파일로 병합한다.
    merged_webm_file_path = CACHE_DIR_PATH / get_temp_file_name("webm")
    ffmpeg.input(str(webm_list_text_file_path), format="concat", safe=0).output(
        str(merged_webm_file_path), c="copy"
    ).run()

    # 3. webm 파일 목록 txt 파일 삭제
    webm_list_text_file_path.unlink()

    # 4. webm 파일 mp3로 변환
    output_mp3_path = CACHE_DIR_PATH / get_temp_file_name("mp3")
    (
        ffmpeg.input(merged_webm_file_path)
        .output(str(output_mp3_path), ar=22050, ab="64k")
        .run()
    )

    # 5. 변환 후 원본 webm 파일 삭제
    merged_webm_file_path.unlink()

    return output_mp3_path


merge_webm_files_to_mp3(
    [
        "/Users/cyh/Downloads/temp/1.webm",
        "/Users/cyh/Downloads/temp/2.webm",
        "/Users/cyh/Downloads/temp/2.webm",
        "/Users/cyh/Downloads/temp/2.webm",
    ]
)
