from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


def _ensure_sqlite_directory(url: str) -> None:
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith("sqlite:////"):
        db_path = Path(url[len(prefix):])
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)


_database_url = get_settings().database_url
_ensure_sqlite_directory(_database_url)
engine = create_engine(
    _database_url,
    connect_args={"check_same_thread": False} if _database_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)

if _database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
