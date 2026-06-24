from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# Ensure the storage directory (and any SQLite parent folder) exists before the
# engine tries to open the database file.
settings.data_path.mkdir(parents=True, exist_ok=True)
if settings.database_url.startswith("sqlite"):
    db_file = settings.database_url.split("sqlite:///", 1)[-1]
    if db_file and db_file != ":memory:":
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

# SQLite needs check_same_thread=False because FastAPI runs requests on a
# threadpool. For other databases the connect_args are ignored.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register with Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()


def _migrate_sqlite_columns() -> None:
    """Add new columns to existing SQLite DBs (create_all does not alter tables)."""
    if not settings.database_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    alters = [
        "ALTER TABLE documents ADD COLUMN summary TEXT",
        "ALTER TABLE documents ADD COLUMN entities_json TEXT",
        "ALTER TABLE documents ADD COLUMN source_url VARCHAR(2048)",
        "ALTER TABLE knowledge_bases ADD COLUMN status VARCHAR(32) DEFAULT 'active'",
        "ALTER TABLE knowledge_bases ADD COLUMN search_provider VARCHAR(64) DEFAULT 'local'",
        "ALTER TABLE knowledge_bases ADD COLUMN index_artifacts INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_bases ADD COLUMN index_wikis INTEGER DEFAULT 0",
    ]
    with engine.begin() as conn:
        for stmt in alters:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
