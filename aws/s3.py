from typing import Optional
import uuid
import logging
import requests

import boto3
from botocore.exceptions import ClientError


def create_presigned_post(
    bucket_name, object_name, fields, conditions, expiration=3600
):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
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

    # The response contains the presigned URL and required fields
    return response


def upload_file_with_presigned_post(url, fields, file_path):
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

    :param bucket_name: 접근할 S3 object가 저장되어 있는 버킷의 이름
    :param object_key: 접근할 S3 object의 key
    :param expiration: URL 만료 시간
    :return: 생성된 presigned URL, 또는 실패했을 경우 None
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
        "key": object_name,
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
