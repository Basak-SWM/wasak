from pathlib import Path
import tempfile

"""
프로젝트에서 사용하는 cache 관련 로직 담당 서비스
"""


def get_cache_file_path(suffix: str):
    """_summary_
    프로젝트에서 사용할 cache 파일의 full path 반환
    * 주의 * 해당 파일은 수동으로 삭제해야 함. 

    Args:
        suffix: 캐시 파일 확장자

    Returns:
        Path: 생성된 Path 객체

    """

    return Path(tempfile.NamedTemporaryFile(suffix=f".{suffix}").name)
