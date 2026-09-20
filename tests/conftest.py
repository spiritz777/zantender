import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.database.base import Base
from app.database.database import create_db_engine, get_session_factory


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        bot_token="test-token",
        gemini_api_key="test-key",
        max_file_size_mb=1,
        chunk_size_chars=80,
        analysis_context_max_chars=500,
    )


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return get_session_factory(engine)
