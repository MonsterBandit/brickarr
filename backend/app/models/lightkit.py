from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LightKitStatus(str, enum.Enum):
    owned = "owned"
    wanted = "wanted"


class LightKit(Base):
    __tablename__ = "light_kit"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    set_no: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[LightKitStatus] = mapped_column(
        Enum(LightKitStatus, name="light_kit_status"), nullable=False, default=LightKitStatus.wanted
    )
    product_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    local_pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
