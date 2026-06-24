from __future__ import annotations

from typing import List

from app.schemas.base import CamelModel


class BuyListLine(CamelModel):
    item_type: str
    item_no: str
    color_id: int
    min_qty: int


class BuyListJson(CamelModel):
    records: List[BuyListLine] = []
