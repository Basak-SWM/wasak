import enum

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    BigInteger,
    Enum,
)

Base = declarative_base()


class AnalysisRecordType(enum.Enum):
    STT = "STT"
    DECIBEL = "DECIBEL"
    HERTZ = "HERTZ"
    WPM = "WPM"
    PAUSE = "PAUSE"


class AnalysisRecord(Base):
    __tablename__ = "analysis_record"
    id = Column(BigInteger, primary_key=True)
    speech_id = Column(Integer, ForeignKey("speech.id"), nullable=False)
    type = Column(Enum(AnalysisRecordType), nullable=False)


class Speech(Base):
    __tablename__ = "speech"
    id = Column(Integer, primary_key=True)


class AudioSegment(Base):
    __tablename__ = "audio_segment"
    id = Column(BigInteger, primary_key=True)
    speech_id = Column(Integer, ForeignKey("speech.id"), nullable=False)
    url = Column(String, name="full_audios3url", nullable=False)

    def __str__(self) -> str:
        return f"AudioSegment(id={self.id}, speech_id={self.speech_id}, url={self.url})"

    def __repr__(self) -> str:
        return self.__str__()

    def get_key(self) -> str:
        return self.url.split("/")[-1]

    def get_full_path(self) -> str:
        return self.url.split(".com/")[-1]
