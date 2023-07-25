from typing import List
from sqlalchemy import BinaryExpression, Engine, create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker


from configs import db
from data.tables import AudioSegment, Speech


class DatabaseClient:
    def __init__(self) -> None:
        self.config: db.DatabaseConfigs = db.DatabaseConfigs()
        self.engine: Engine = create_engine(
            self.config.get_full_url(), pool_size=20, pool_recycle=500, max_overflow=20
        )

    def get_session(self) -> Session:
        return scoped_session(sessionmaker(bind=self.engine))()

    def select_all(self, table_class: type) -> List[type]:
        session = self.get_session()
        _query = session.query(table_class)
        result = _query.all()
        session.close()

        return result

    def conditional_select_all(
        self, table_class: type, conditions: List[BinaryExpression[bool]]
    ) -> List[type]:
        session = self.get_session()
        _query = session.query(table_class)

        for condition in conditions:
            _query = _query.filter(condition)

        result = _query.all()
        session.close()

        return result


class AudioSegmentDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__()

    def select_audio_segments_of(self, speech: Speech) -> List[AudioSegment]:
        return super().conditional_select_all(
            AudioSegment, [AudioSegment.speech_id.bool_op("=")(speech.id)]
        )
