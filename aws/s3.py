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

    print("URL:", url)
    print("fields:", fields)
    print("Object key:", fields["key"])
    upload_file_with_presigned_post(url, fields, "./resource/test/audio/1_100.mp3")
