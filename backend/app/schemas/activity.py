from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.base import CamelModel


class QueueItem(CamelModel):
    job_id: str
    name: Optional[str] = None
    status: str
    progress_bytes: int = 0
    total_bytes: int = 0
    error: Optional[str] = None


class QueueEnvelope(CamelModel):
    records: List[QueueItem] = []


class HistoryItem(CamelModel):
    job_id: str
    event_type: str
    name: Optional[str] = None
    status: str
    message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class HistoryEnvelope(CamelModel):
    page: int = 1
    page_size: int = 50
    total_records: int = 0
    records: List[HistoryItem] = []
