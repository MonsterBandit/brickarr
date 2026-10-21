from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CHAR, DECIMAL, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, BigIntPK
from app.models.catalog import ItemType


class GuideType(str, enum.Enum):
    sold = "sold"
    stock = "stock"


class PriceCondition(str, enum.Enum):
    new = "new"
    used = "used"


class PriceCache(Base):
    __tablename__ = "price_cache"
    __table_args__ = (
        UniqueConstraint(
            "item_type", "item_no", "color_id", "guide_type", "condition", "currency",
            name="uq_price_cache_row",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType, name="price_item_type", native_enum=False), nullable=False)
    item_no: Mapped[str] = mapped_column(String(32), nullable=False)
    color_id: Mapped[Optional[int]] = mapped_column(ForeignKey("color.color_id"), nullable=True)
    guide_type: Mapped[GuideType] = mapped_column(Enum(GuideType, name="price_guide_type", native_enum=False), nullable=False)
    condition: Mapped[PriceCondition] = mapped_column(Enum(PriceCondition, name="price_condition", native_enum=False), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    min_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), nullable=True)
    max_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), nullable=True)
    avg_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), nullable=True)
    qty_avg_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4), nullable=True)
    unit_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ttl_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
