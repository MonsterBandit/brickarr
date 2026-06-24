from __future__ import annotations

from typing import List, Optional

from app.schemas.base import CamelModel


class PartLine(CamelModel):
    set_part_id: int
    part_no: str
    part_item_type: str
    name: Optional[str] = None
    color_id: int
    color_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    quantity: int
    extra_quantity: int
    owned: int
    missing: int
    is_alternate: bool
    is_counterpart: bool
    match_no: int


class PartsEnvelope(CamelModel):
    records: List[PartLine] = []


class OwnershipPatch(CamelModel):
    set_part_id: Optional[int] = None
    part_no: Optional[str] = None
    color_id: Optional[int] = None
    quantity_owned: int


class MinifigLine(CamelModel):
    set_part_id: int
    part_no: str
    name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    quantity: int
    owned: int
    missing: int


class MinifigsEnvelope(CamelModel):
    records: List[MinifigLine] = []


class PartPrice(CamelModel):
    available: bool = False
    part_no: Optional[str] = None
    color_id: Optional[int] = None
    guide_type: Optional[str] = None
    condition: Optional[str] = None
    currency: Optional[str] = None
    min_price: Optional[float] = None
    avg_price: Optional[float] = None
    qty_avg_price: Optional[float] = None
