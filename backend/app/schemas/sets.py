from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.schemas.base import CamelModel


class SetStats(CamelModel):
    owned: int = 0
    missing: int = 0
    price_per_piece: Optional[Decimal] = None


class SetLinks(CamelModel):
    bricklink: str


class SetSummary(CamelModel):
    id: int
    item_type: str = "SET"
    set_number: str
    name: Optional[str] = None
    status: str
    theme: Optional[str] = None
    year: Optional[int] = None
    pieces: Optional[int] = None
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None


class SetDetail(CamelModel):
    id: int
    item_type: str = "SET"
    set_number: str
    name: Optional[str] = None
    status: str
    condition: Optional[str] = None
    copies: int = 1
    storage_location: Optional[str] = None
    theme: Optional[str] = None
    subtheme: Optional[str] = None
    year: Optional[int] = None
    pieces: Optional[int] = None
    minifigs: Optional[int] = None
    rrp: Optional[Decimal] = None
    acquired_price: Optional[Decimal] = None
    acquired_date: Optional[date] = None
    launch_date: Optional[date] = None
    exit_date: Optional[date] = None
    image_url: Optional[str] = None
    stats: SetStats = Field(default_factory=SetStats)
    current_value: Optional[Decimal] = None
    gain_loss: Optional[Decimal] = None
    links: SetLinks


class SetCreate(CamelModel):
    set_number: str
    status: str = "collecting"
    condition: Optional[str] = None
    copies: int = 1
    storage_location: Optional[str] = None
    acquired_price: Optional[Decimal] = None
    acquired_date: Optional[date] = None
    notes: Optional[str] = None


class SetPatch(CamelModel):
    status: Optional[str] = None
    condition: Optional[str] = None
    copies: Optional[int] = None
    storage_location: Optional[str] = None
    acquired_price: Optional[Decimal] = None
    acquired_date: Optional[date] = None
    notes: Optional[str] = None


class SetLookupRecord(CamelModel):
    item_type: str
    set_number: str
    name: Optional[str] = None
    year: Optional[int] = None
    theme: Optional[str] = None
    thumbnail_url: Optional[str] = None
    owned: bool = False


class SetLookupEnvelope(CamelModel):
    page: int = 1
    page_size: int = 50
    total_records: int = 0
    records: list[SetLookupRecord] = []
    warning: Optional[str] = None


class OwnedItemOut(CamelModel):
    id: int
    item_type: str
    item_no: str
    status: str
    copies: int
    condition: Optional[str] = None
    storage_location: Optional[str] = None
    acquired_price: Optional[Decimal] = None
    acquired_date: Optional[date] = None
    notes: Optional[str] = None
    date_added: datetime
