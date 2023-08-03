import enum


class AnalysisRecordType(enum.Enum):
    STT = "STT"
    DECIBEL = "DECIBEL"
    HERTZ = "HERTZ"
    LPM = "LPM"
    LPM_AVG = "LPM_AVG"
    PAUSE = "PAUSE"
    PAUSE_RATIO = "PAUSE_RATIO"
