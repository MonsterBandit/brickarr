from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.base import CamelModel


class QueueItem(CamelModel):
    id: int
    name: str
    kind: str
    status: str
    progress: int = 0
    total: int = 0
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None


class QueueEnvelope(CamelModel):
    records: List[QueueItem] = []


class HistoryItem(CamelModel):
    id: int
    name: str
    kind: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class HistoryEnvelope(CamelModel):
    page: int = 1
    page_size: int = 50
    total_records: int = 0
    records: List[HistoryItem] = []
