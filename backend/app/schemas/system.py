from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.base import CamelModel


class SourceReachability(CamelModel):
    brickset: Optional[bool] = None


class SystemStatus(CamelModel):
    version: str
    db_type: str
    db_ok: bool
    sources: SourceReachability


class TaskInfo(CamelModel):
    name: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class TasksEnvelope(CamelModel):
    records: List[TaskInfo] = []


class CommandRequest(CamelModel):
    name: str


class CommandAccepted(CamelModel):
    job_id: int
    name: str
    status: str = "queued"
