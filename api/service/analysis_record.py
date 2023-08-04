import datetime
from typing import Any
import json
from api.data.client import AnalysisRecordDatabaseClient

from api.data.enums import AnalysisRecordType
from api.service.aws.s3 import S3Service


class AnalysisRecordService:
    def __init__(self) -> None:
        self.s3_service = S3Service()
        self.db_client = AnalysisRecordDatabaseClient()

    def save_analysis_result(
        self,
        presentation_id: int,
        speech_id: int,
        record_type: AnalysisRecordType,
        result: Any,
    ) -> None:
        result_key = f"{presentation_id}/{speech_id}/analysis/{record_type.value}.json"
        self.s3_service.upload_json_object(result_key, json.dumps(result))
        self.db_client.create(
            record_type=record_type.value,
            speech_id=speech_id,
            url=self.s3_service.get_presigned_url(result_key),
            created_date=datetime.datetime.now(),
        )
