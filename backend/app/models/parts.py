from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, BigIntPK


class PartItemType(str, enum.Enum):
    PART = "PART"
    MINIFIG = "MINIFIG"


class SetPart(Base):
    __tablename__ = "set_part"
    __table_args__ = (
        ForeignKeyConstraint(
            ["part_item_type", "part_no"],
            ["catalog_item.item_type", "catalog_item.item_no"],
            name="fk_set_part_catalog",
        ),
        UniqueConstraint(
            "set_no", "match_no", "part_item_type", "part_no", "color_id", "is_alternate", "is_counterpart",
            name="uq_set_part_line",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    set_no: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    part_item_type: Mapped[PartItemType] = mapped_column(Enum(PartItemType, name="part_item_type", native_enum=False), nullable=False)
    part_no: Mapped[str] = mapped_column(String(32), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("color.color_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extra_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_alternate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_counterpart: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
