from __future__ import annotations

from app.schemas.base import CamelModel


class HealthItem(CamelModel):
    source: str
    type: str
    message: str
