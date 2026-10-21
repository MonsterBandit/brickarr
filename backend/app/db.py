from __future__ import annotations

from typing import Any, Generator

from sqlalchemy import BigInteger, Integer, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite only auto-numbers an INTEGER PRIMARY KEY (the rowid); a BIGINT key
# would make every insert fail. MariaDB keeps BIGINT.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    pass


def _sqlite_on_connect(dbapi_connection: Any, _record: Any) -> None:
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA journal_mode=WAL")
    cur.close()


def make_engine(**kwargs: Any) -> Engine:
    """The one engine factory, shared by the app and Alembic."""
    if settings.db_type == "sqlite":
        eng = create_engine(settings.db_url, connect_args={"check_same_thread": False}, **kwargs)
        event.listen(eng, "connect", _sqlite_on_connect)
        return eng
    return create_engine(settings.db_url, pool_pre_ping=True, **kwargs)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
