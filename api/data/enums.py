import enum


class AnalysisRecordType(enum.Enum):
    STT = "STT"
    DECIBEL = "DECIBEL"
    HERTZ = "HERTZ"
    HERTZ_AVG = "HERTZ_AVG"
    LPM = "LPM"
    LPM_AVG = "LPM_AVG"
    PAUSE = "PAUSE"
    PAUSE_RATIO = "PAUSE_RATIO"
    SPEECH_CORRECTION = "SPEECH_CORRECTION"


class SpeechCorrectionType(enum.Enum):
    TOO_FAST = "TOO_FAST"
    TOO_SLOW = "TOO_SLOW"
    PAUSE_TOO_LONG = "PAUSE_TOO_LONG"
    PAUSE_TOO_SHORT = "PAUSE_TOO_SHORT"


class AIChatLogRole(enum.Enum):
    SYSTEM = "system"
    AI = "ai"
    HUMAN = "human"


class AIChatLogStatus(enum.Enum):
    WAIT = "WAIT"
    DONE = "DONE"
    ERROR = "ERROR"
