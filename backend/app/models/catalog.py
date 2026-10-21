from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CHAR, DECIMAL, DateTime, Enum, Integer, SmallInteger, String, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ItemType(str, enum.Enum):
    SET = "SET"
    MINIFIG = "MINIFIG"
    PART = "PART"


class CatalogItem(Base):
    __tablename__ = "catalog_item"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType, name="catalog_item_type", native_enum=False), primary_key=True)
    item_no: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    year_released: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    weight_g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    dim_x_cm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    dim_y_cm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    dim_z_cm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    rebrickable_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    theme: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    subtheme: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    rrp: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    launch_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age_min: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    age_max: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    num_pieces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_minifigs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2), nullable=True)
    brickset_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    catalog_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    brickset_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Color(Base):
    __tablename__ = "color"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    color_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    rgb: Mapped[Optional[str]] = mapped_column(CHAR(6), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
