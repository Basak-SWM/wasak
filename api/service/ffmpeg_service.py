import ffmpeg
from pathlib import Path
from typing import List

from api.service.cache_service import get_cache_file_path

"""
*주의* ffmpeg가 OS의 PATH에 등록되어 있어야 함.
"""


def merge_webm_files_to_wav_ffmpeg(webm_files_path_list: List[str]) -> str:
    """_summary_
    여러 webm 파일을 하나의 wav 파일로 병합한다.

    Args:
        webm_files_path_list (List[str]): Segment webm 파일들의 경로를 담은 list

    Raises:
        FileNotFoundError: 제공된 Segment webm 파일 경로가 올바르지 않을 경우

    Returns:
        Path: 생성된 wav 파일 경로 (S3 업로드 후 해당 파일 삭제해야 함.)
    """

    # 1. 병합 대상 webm 파일들의 절대 경로들을 txt 파일에 기록한다.
    webm_list_text_file_path = get_cache_file_path("txt")

    with open(webm_list_text_file_path, "w") as f:
        for item in webm_files_path_list:
            if (target_path := Path(item)).is_file():
                f.write(f"file '{target_path}'\n")
            else:
                raise FileNotFoundError(
                    f"Audio Segment File {target_path} is not found."
                )

    # 2. ffmpeg로 음성 파일 목록 txt 파일 읽어서 하나의 webm 파일로 병합한다.
    merged_webm_file_path = get_cache_file_path("webm")
    ffmpeg.input(str(webm_list_text_file_path), format="concat", safe=0).output(
        str(merged_webm_file_path), c="copy"
    ).global_args("-loglevel", "error").run()

    # 3. webm 파일 목록 txt 파일 삭제
    webm_list_text_file_path.unlink()

    # 4. webm 파일 wav 변환
    output_wav_path = get_cache_file_path("wav")
    (
        ffmpeg.input(str(merged_webm_file_path))
        .output(str(output_wav_path))
        .global_args("-loglevel", "error")
        .run()
    )

    # 5. 변환 후 병합된 원본 webm 파일 삭제
    merged_webm_file_path.unlink()

    return output_wav_path


def merge_webm_files_to_wav_binary_concat(webm_files_path_list: List[str]) -> Path:
    """
    _summary_
    단순 binary concat 방식으로 webm 파일들을 하나의 webm 파일로 병합한다.

    Args:
        webm_files_path_list (Path): webm 파일 경로

    Returns:
        Path: 병합된 webm 파일 경로

    """
    merged_webm_path = get_cache_file_path("webm")
    with open(merged_webm_path, "wb") as f:
        for webm_file_path in webm_files_path_list:
            with open(webm_file_path, "rb") as f2:
                f.write(f2.read())

    return merged_webm_path


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


if __name__ == "__main__":
    print(
        merge_webm_files_to_wav_binary_concat(
            [
                '/Users/cyh/Downloads/debug_audio/1691069794891_bb36af31-c176-4c1d-9d66-444a4ef58092.webm',
                '/Users/cyh/Downloads/debug_audio/1691069797883_7f61c544-6913-4bf2-b16c-58d9d3ce8846.webm',
                '/Users/cyh/Downloads/debug_audio/1691069800894_1c0e2297-053a-4d98-b312-27c902d48ed5.webm',
                '/Users/cyh/Downloads/debug_audio/1691069803955_1052d7c2-ca57-4c42-81ae-6414e4422aae.webm',
                '/Users/cyh/Downloads/debug_audio/1691069805056_3642c3be-7e78-4029-a977-a9aa2a629853.webm'
            ]
        )
    )
