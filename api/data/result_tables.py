import enum
from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Integer, Text
from api.data.tables import CreatedDateMixin

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AnalysisRecordType(enum.Enum):
    STT = "STT"
    DECIBEL = "DECIBEL"
    HERTZ = "HERTZ"
    WPM = "WPM"
    PAUSE = "PAUSE"


class AnalysisRecord(CreatedDateMixin, Base):
    __tablename__ = "analysis_record"
    id = Column(BigInteger, primary_key=True)
    speech_id = Column(Integer, ForeignKey("speech.id"), nullable=False)
    type = Column(Enum(AnalysisRecordType), nullable=False)


class STTResult(CreatedDateMixin, Base):
    __tablename__ = "stt_result"
    id = Column(BigInteger, primary_key=True)
    body = Column(Text, nullable=False)


class HertzAnalysisResult(CreatedDateMixin, Base):
    __tablename__ = "hertz_analysis_result"
    id = Column(BigInteger, primary_key=True)
    body = Column(Text, nullable=False)


class WpmAnalysisResult(CreatedDateMixin, Base):
    __tablename__ = "wpm_analysis_result"
    id = Column(BigInteger, primary_key=True)
    body = Column(Text, nullable=False)


class PauseAnalysisResult(CreatedDateMixin, Base):
    __tablename__ = "pause_analysis_result"
    id = Column(BigInteger, primary_key=True)
    body = Column(Text, nullable=False)
