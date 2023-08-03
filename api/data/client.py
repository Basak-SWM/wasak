from typing import List, TypeVar, Optional
from sqlalchemy import BinaryExpression, Engine, create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, scoped_session, sessionmaker


from api.configs import db
from api.data.tables import AudioSegment, Speech


T = TypeVar("T")


class DatabaseClient:
    def __init__(self, table_class: T) -> None:
        self.config: db.DatabaseConfigs = db.config
        self.engine: Engine = create_engine(
            self.config.get_full_url(), pool_size=20, pool_recycle=500, max_overflow=20
        )
        self.table_class = table_class

    def get_session(self) -> Session:
        return scoped_session(sessionmaker(bind=self.engine))()

    def select_all(self) -> List[T]:
        session = self.get_session()
        _query = session.query(self.table_class)
        result = _query.all()
        session.close()

        return result

    def conditional_select_all(
        self, conditions: List[BinaryExpression[bool]]
    ) -> List[T]:
        session = self.get_session()
        _query = session.query(self.table_class)

        for condition in conditions:
            _query = _query.filter(condition)

        result = _query.all()
        session.close()

        return result

    def get_single(self, conditions: List[BinaryExpression[bool]]) -> Optional[T]:
        session = self.get_session()
        _query = session.query(self.table_class)

        for condition in conditions:
            _query = _query.filter(condition)

        try:
            result = _query.one()
        except NoResultFound:
            session.close()
            return None
        else:
            session.close()
            return result

    def insert(self, vo: T) -> T:
        vo.id = None

        session = self.get_session()
        session.add(vo)
        session.commit()
        session.close()

        return vo

    def update(self, vo: T) -> T:
        session = self.get_session()
        session.merge(vo)
        session.commit()
        session.close()

        return vo


class SpeechDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(Speech)


class AudioSegmentDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        super().__init__(AudioSegment)

    def select_audio_segments_of(self, speech: Speech) -> List[AudioSegment]:
        return super().conditional_select_all(
            [AudioSegment.speech_id.bool_op("=")(speech.id)]
        )
