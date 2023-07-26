from api.data.client import DatabaseClient
from api.data.result_tables import (
    AnalysisRecord,
    DecibelAnalysisResult,
    HertzAnalysisResult,
    PauseAnalysisResult,
    STTResult,
    WpmAnalysisResult,
)


class AnalysisRecordDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(AnalysisRecord)


class STTResultDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(STTResult)


class DecibelAnalysisDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(DecibelAnalysisResult)


class HertzAnalysisDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(HertzAnalysisResult)


class WpmAnalysisDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(WpmAnalysisResult)


class PauseAnalysisDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(PauseAnalysisResult)
