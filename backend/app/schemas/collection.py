from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.schemas.base import CamelModel


class CollectionCounts(CamelModel):
    sets: int = 0
    minifigs: int = 0
    parts: int = 0


class CollectionValue(CamelModel):
    counts: CollectionCounts
    rrp_total: Optional[Decimal] = None
    acquired_total: Optional[Decimal] = None
    current_value_total: Optional[Decimal] = None
    gain_loss_total: Optional[Decimal] = None
