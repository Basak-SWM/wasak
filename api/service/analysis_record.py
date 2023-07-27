from typing import Any
import json

from api.data.tables import Speech
from api.data.enums import AnalysisRecordType
from api.service.aws.s3 import S3Service


class AnalysisRecordService:
    def __init__(self) -> None:
        self.s3_service = S3Service()

    def save_analysis_result(
        self, speech: Speech, record_type: AnalysisRecordType, result: Any
    ) -> None:
        result_key = (
            f"{speech.presentation_id}/{speech.id}/analysis/{record_type.value}.json"
        )
        self.s3_service.upload_json_object(result_key, json.dumps(result))
