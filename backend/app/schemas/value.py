from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.schemas.base import CamelModel


class ValueLinks(CamelModel):
    price_guide: str
    items_for_sale: str
    part_out_value: str


class SetValue(CamelModel):
    rrp: Optional[Decimal] = None
    links: ValueLinks
    computed: Optional[dict] = None
