import datetime
import os
from pathlib import Path
import uuid
"""
프로젝트에서 사용하는 cache 관련 로직 담당 서비스
"""

# 항상 동일한 cache 폴더 경로를 갖기 위해 __file__ 기준으로 경로를 설정한다.
PROJECT_ROOT_PATH = Path(os.path.realpath(__file__)).parent.parent
CACHE_DIR_PATH = (PROJECT_ROOT_PATH / "cache").resolve()

# 존재하지 않을 시에만 cache 폴더 생성
CACHE_DIR_PATH.mkdir(parents=True, exist_ok=True)


def get_cache_folder_path():
    return CACHE_DIR_PATH


def get_cache_file_path(suffix: str):
    """_summary_
    프로젝트에서 사용할 cache 파일의 랜덤한 full path를 반환한다.
    형식: {cache path}/{timestamp}_{uuid}.{suffix}

    Args:
        suffix: 캐시 파일 확장자

    Returns:
        Path: 생성된 Path 객체

    """
    timestamp_string = datetime.datetime.now().strftime("%Y%m%d%H%M")
    uuid_string = uuid.uuid4()

    return CACHE_DIR_PATH / f"{timestamp_string}_{uuid_string}.{suffix}"
