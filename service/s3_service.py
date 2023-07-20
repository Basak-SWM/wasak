from typing import List
import boto3
from cache_service import get_cache_file_path


def download_webm_segments_from_speech_info(s3_webm_segments_path_list: List[str]):
    s3 = boto3.client("s3")
    downloaded_webm_files_path = []

    for item in s3_webm_segments_path_list:
        download_destination_path = get_cache_file_path("webm")
        # TODO:
        # s3.download_file("bucket_name", item, download_destination_path)
        downloaded_webm_files_path.append(download_destination_path)
