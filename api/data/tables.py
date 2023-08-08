from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    ForeignKey,
    BigInteger,
    func,
)

from api.data.enums import AnalysisRecordType

Base = declarative_base()


class CreatedDateMixin:
    created_date = Column(DateTime(), default=func.now())


class FullDateMixin(CreatedDateMixin):
    last_modified_date = Column(DateTime(), default=func.now())


class Presentation(FullDateMixin, Base):
    __tablename__ = "presentation"
    id = Column(Integer, primary_key=True)


class Speech(FullDateMixin, Base):
    __tablename__ = "speech"
    id = Column(Integer, primary_key=True)
    presentation_id = Column(Integer, ForeignKey("presentation.id"), nullable=False)
    full_audios3url = Column(String, nullable=True)
    avgf0 = Column(Float, nullable=True)
    avglpm = Column(Float, nullable=True)
    feedback_count = Column(Integer, nullable=True)
    pause_ratio = Column(Float, nullable=True)


class AudioSegment(CreatedDateMixin, Base):
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


class AnalysisRecord(CreatedDateMixin, Base):
    __tablename__ = "analysis_record"
    id = Column(Integer, primary_key=True)
    record_type = Column(Enum(AnalysisRecordType), name="type", nullable=False)
    speech_id = Column(Integer, ForeignKey("speech.id"), nullable=False)
    url = Column(String, name="url", nullable=False)
