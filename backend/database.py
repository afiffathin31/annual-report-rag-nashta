"""Database configuration and session management with Dual-Engine support (SQLite / PostgreSQL)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_PATH = DATA_DIR / "nashta_intelligence.db"

# Load database URL from environment or default to local SQLite with FTS5
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

# Engine options
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL connection pool settings
    engine_args["pool_size"] = 15
    engine_args["max_overflow"] = 25
    engine_args["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_args)

# SQLite Performance Pragmas (WAL mode for fast multi-reader concurrent queries)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA temp_store=MEMORY")
        except Exception:
            pass
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all registered tables and virtual tables if they don't exist."""
    import backend.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    
    # Initialize SQLite FTS5 table if using SQLite
    if DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                        chunk_id UNINDEXED,
                        emiten_code UNINDEXED,
                        chapter_title,
                        raw_paragraph,
                        tokenize = 'porter unicode61'
                    );
                    """
                )
                conn.commit()
            except Exception:
                # FTS table might already exist or handled by repository
                pass
