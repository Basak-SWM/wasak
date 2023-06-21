from typing import Dict, Optional, List
import uuid
import logging
import requests

import boto3
from botocore.exceptions import ClientError


def create_presigned_post(
    bucket_name: str,
    object_name: str,
    fields: dict,
    conditions: List[dict],
    expiration: Optional[int] = 3600,
) -> Optional[dict]:
    """
    S3에 파일을 업로드하기 위한 Presigned POST URL을 생성하는 함수
    참고: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_post.html

    :param bucket_name: 파일을 업로드할 버킷의 이름
    :param object_name: 업로드할 object의 이름
    :param fields: 파일 업로드에 필요한 추가 정보
    :param conditions: Policy에 포함할 condition 목록
    :param expiration: URL 만료 시간 (초)
    :return: 다음 key를 가지는 딕셔너리:
        url: 파일 업로드에 사용할 URL
        fields: POST method로 파일을 업로드할 때 HTTP Body로 전달해야 할 값들을 포함하는 딕셔너리
    :return: 에러가 발생할 경우 None
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response


def upload_file_with_presigned_post(url: str, fields: dict, file_path: str):
    """
    `create_presigned_post`로 발급받은 presigned POST URL에 파일을 업로드하는 함수

    :param url: 발급받은 presigned POST URL
    :param fields: 발급받은 presigned POST fields
    :file_path: 업로드할 파일의 경로
    """
    with open(file_path, "rb") as file:
        files = {"file": file}

        try:
            response = requests.post(url, data=fields, files=files)
            response.raise_for_status()
            print("File upload successful!")
        except requests.exceptions.RequestException as e:
            print("File upload failed:", e)


def generate_presigned_url(
    bucket_name: str, object_key: str, expiration: Optional[int] = 3600
) -> Optional[str]:
    """
    제한된 시간(expiration) 동안 특정 S3 object에 접근할 수 있는 presigned URL을 생성하는 함수
    참고: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html

    :param bucket_name: 접근할 S3 object가 저장되어 있는 버킷의 이름
    :param object_key: 접근할 S3 object의 key
    :param expiration: URL 만료 시간 (초)
    :return: 생성된 presigned URL
    :return: 에러 발생시 None
    """
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
        return response
    except ClientError as e:
        print("Error generating presigned URL: {}".format(e))
        return None


if __name__ == "__main__":
    bucket_name = "tokpeanut"
    prefix = str(uuid.uuid4())
    object_name = prefix + "_" + input("Object name : ")

    fields = {
        "Content-Type": "audio/mpeg",
        "acl": "private",
    }

    conditions = [
        {"Content-Type": "audio/mpeg"},
        {"acl": "private"},
        ["content-length-range", 0, 10485760],
    ]

    expiration = 360000

    result = create_presigned_post(
        bucket_name, object_name, fields, conditions, expiration
    )

    url = result["url"]
    fields = result["fields"]
    key = fields["key"]

    print("URL:", url)
    print("fields:", fields)
    print("Object key:", key)
    upload_file_with_presigned_post(url, fields, "./resource/test/audio/1_100.mp3")

    access_url = generate_presigned_url("tokpeanut", key, 30)
    print("Presigned url for access file:", access_url)
