from sqlalchemy import inspect

from app.database.base import Base
from app.database.database import create_db_engine
from app.database.models import User


def test_initial_schema_contains_required_tables() -> None:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == {
        "analyses",
        "company_profiles",
        "conversations",
        "document_chunks",
        "documents",
        "messages",
        "notification_preferences",
        "tenders",
        "users",
    }


def test_telegram_id_is_unique() -> None:
    table = User.__table__
    assert any(column.unique for column in table.columns if column.name == "telegram_id")
