from typing import Any
import json

from api.data.client import AnalysisRecordDatabaseClient
from api.data.result_client import (
    DecibelAnalysisDatabaseClient,
    HertzAnalysisDatabaseClient,
    PauseAnalysisDatabaseClient,
    STTResultDatabaseClient,
    WpmAnalysisDatabaseClient,
)
from api.data.tables import Speech
from api.data.result_tables import (
    AnalysisRecord,
    AnalysisRecordType,
    DecibelAnalysisResult,
    HertzAnalysisResult,
    PauseAnalysisResult,
    STTResult,
    WpmAnalysisResult,
)


class AnalysisRecordService:
    def __init__(self) -> None:
        self.analysis_record_db_client = AnalysisRecordDatabaseClient()
        self.result_clients = {
            AnalysisRecordType.STT: STTResultDatabaseClient(),
            AnalysisRecordType.DECIBEL: DecibelAnalysisDatabaseClient(),
            AnalysisRecordType.HERTZ: HertzAnalysisDatabaseClient(),
            AnalysisRecordType.WPM: WpmAnalysisDatabaseClient(),
            AnalysisRecordType.PAUSE: PauseAnalysisDatabaseClient(),
        }

    def save_analysis_result(
        self, speech: Speech, record_type: AnalysisRecordType, result: Any
    ) -> None:
        vo = self.convert_as_vo(speech, record_type, result)
        self.result_clients[record_type].insert(vo)

        record = AnalysisRecord(speech_id=speech.id, type=record_type)
        self.analysis_record_db_client.insert(record)

    def convert_as_vo(
        self, speech: Speech, record_type: AnalysisRecordType, result: Any
    ):
        json_stringified_result = json.dumps(result)

        if record_type == AnalysisRecordType.STT:
            return STTResult(speech_id=speech.id, body=json_stringified_result)
        elif record_type == AnalysisRecordType.DECIBEL:
            return DecibelAnalysisResult(
                speech_id=speech.id, body=json_stringified_result
            )
        elif record_type == AnalysisRecordType.HERTZ:
            return HertzAnalysisResult(
                speech_id=speech.id, body=json_stringified_result
            )
        elif record_type == AnalysisRecordType.WPM:
            return WpmAnalysisResult(speech_id=speech.id, body=json_stringified_result)
        elif record_type == AnalysisRecordType.PAUSE:
            return PauseAnalysisResult(
                speech_id=speech.id, body=json_stringified_result
            )
        else:
            raise Exception("Unhandled AnalysisRecordType: " + record_type)
