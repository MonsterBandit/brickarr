from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DECIMAL, Date, DateTime, Enum, ForeignKeyConstraint, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, BigIntPK
from app.models.catalog import ItemType


class OwnedStatus(str, enum.Enum):
    collecting = "collecting"
    complete = "complete"
    wanted = "wanted"
    dismantled = "dismantled"


class OwnedCondition(str, enum.Enum):
    new = "new"
    used = "used"


class OwnedItem(Base):
    __tablename__ = "owned_item"
    __table_args__ = (
        ForeignKeyConstraint(
            ["item_type", "item_no"],
            ["catalog_item.item_type", "catalog_item.item_no"],
            name="fk_owned_item_catalog",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType, name="owned_item_type", native_enum=False), nullable=False)
    item_no: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[OwnedStatus] = mapped_column(
        Enum(OwnedStatus, name="owned_status", native_enum=False), nullable=False, default=OwnedStatus.collecting
    )
    copies: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    condition: Mapped[Optional[OwnedCondition]] = mapped_column(
        Enum(OwnedCondition, name="owned_condition", native_enum=False), nullable=True
    )
    storage_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    acquired_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    acquired_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_added: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
