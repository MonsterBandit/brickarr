from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, BigIntPK


class Ownership(Base):
    __tablename__ = "ownership"
    __table_args__ = (
        UniqueConstraint("owned_item_id", "copy_index", "set_part_id", name="uq_ownership_row"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    owned_item_id: Mapped[int] = mapped_column(ForeignKey("owned_item.id"), nullable=False)
    copy_index: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    set_part_id: Mapped[int] = mapped_column(ForeignKey("set_part.id"), nullable=False)
    quantity_owned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
