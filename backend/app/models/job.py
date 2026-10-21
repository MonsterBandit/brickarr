from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, BigIntPK


# Runtime table not in DATA_MODEL.md: one row per job, queued to finished.
# Replaces the Redis job hashes and the old job_history table (BR.DK.02).
# Resuming after a restart and scheduled tasks are BR.DK.04.
class Job(Base):
    __tablename__ = "job"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
