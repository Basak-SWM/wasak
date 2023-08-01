import json
from typing import Any, Tuple

import boto3

from api.configs.aws.s3 import config as s3_config


class S3Service:
    def __init__(self) -> None:
        self.client = boto3.client("s3")
        self.config = s3_config

    def get_default_bucket_name(self) -> str:
        return self.config.audio_bucket_name

    def upload_object(
        self, upload_file_path: str, object_key: str, *path: Tuple[Any]
    ) -> None:
        """버킷에 파일을 업로드한다.

        Args:
            upload_file_path (str): 업로드할 파일이 저장된 경로
            object_name (str): 저장할 파일의 이름
            *path (Tuple[Any]): 파일의 앞에 붙을 prefix를 나열
        """
        object_path = "/".join(map(str, path))
        key = f"{object_path}/{object_key}" if path else object_key

        self.client.upload_file(upload_file_path, self.get_default_bucket_name(), key)

    def upload_json_object(
        self, object_key: str, json_object: Any, *path: Tuple[Any]
    ) -> None:
        """버킷에 JSON object를 업로드한다.

        Args:
            object_key (str): 저장할 파일의 이름
            json_object (Any): JSON object
            *path (Tuple[Any]): 파일의 앞에 붙을 prefix를 나열
        """
        object_path = "/".join(map(str, path))
        key = f"{object_path}/{object_key}" if path else object_key

        if not (isinstance(json_object, bytes) or isinstance(json_object, bytearray)):
            json_object = json.dumps(json_object, ensure_ascii=False)

        ret = self.client.put_object(
            Bucket=self.get_default_bucket_name(),
            Key=key,
            Body=json_object,
            ContentType="application/json",
        )

    def download_json_object(self, object_key: str) -> Any:
        """버킷에서 JSON object를 다운로드한다.

        Args:
            object_key (str): 다운로드할 파일의 이름

        Returns:
            Any(정상적으로 stt 결과 로드되었다면 dict): 다운로드된 JSON object
        """
        bucket_name = self.get_default_bucket_name()
        response = self.client.get_object(Bucket=bucket_name, Key=object_key)
        str_result = response["Body"].read().decode("utf-8")
        return json.loads(str_result)

    def download_object(self, obj_full_path: str, dest_path: str) -> str:
        """특정 S3 object 하나를 파일 시스템에 다운로드한다.

        Args:
            obj_full_path (str): Object가 버킷 내에서 저장된 위치
            dest_path (str): 다운로드한 파일을 저장할 경로

        Returns:
            str: 다운로드된 파일의 경로
        """
        bucket_name = self.get_default_bucket_name()
        self.client.download_file(bucket_name, obj_full_path, dest_path)
        return dest_path
