import logging
import boto3
from botocore.exceptions import ClientError


def create_presigned_post(
    bucket_name: str,
    object_name: str,
    fields: dict = None,
    conditions=None,
    expiration=3600,
):
    """파일을 업로드하기 위한 사전인증 URL S3 POST 요청 생성하기

    :param bucket_name: 문자열
    :param object_name: 문자열
    :param fields: 미리채워진 양식필드 딕셔너리
    :param conditions: 정책에 포함할 조건 목록
    :param expiration: 사전인증 URL이 유효한 시간 (밀리초)
    :return: 아래의 키를 가진 딕셔너리
        url: POST 요청 URL
        fields: POST와 함께 제출될 양식 항목과 값의 딕셔너리
    :return : 오류시 None
    """

    # 사전인증 S3 POST URL 생성하기
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
    else:
        # 사전인증 URL과 요구되는 항목을 포함한 응답
        return response


if __name__ == "__main__":
    bucket_name = "tokpeanut"
    object_name = input("Object name : ")
    save_fields = dict()
    expires_in = 360000

    result = create_presigned_post(
        bucket_name, object_name, fields=save_fields, expiration=expires_in
    )

    url = result["url"]
    fields = result["fields"]
    print("Created Presigned URL :", url)
    print("fields:", fields)
