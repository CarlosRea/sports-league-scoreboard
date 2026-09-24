import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def create_db_engine(database_url: str):
    """
    Database-agnostic SQLAlchemy engine factory.
    Automatically handles SQLite specifics (threading, foreign keys, StaticPool for memory)
    and production RDBMS settings (connection pooling, pre-ping).
    """
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        is_memory = ":memory:" in database_url or "mode=memory" in database_url
        if is_memory:
            engine = create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        else:
            engine = create_engine(
                database_url,
                connect_args=connect_args,
            )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        return engine
    else:
        # PostgreSQL, MySQL, CockroachDB, etc.
        return create_engine(
            database_url,
            pool_pre_ping=True,
        )


# Initialize engine and session factory with the configured DATABASE_URL
engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def configure_database(database_url: str):
    """Dynamically reconfigure the engine and sessionmaker (e.g. for testing environments)."""
    global engine, SessionLocal
    engine = create_db_engine(database_url)
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )
    return engine


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for obtaining a database session."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
