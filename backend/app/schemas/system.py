from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.schemas.base import CamelModel


class SourceReachability(CamelModel):
    bricklink: Optional[bool] = None
    brickset: Optional[bool] = None


class SystemStatus(CamelModel):
    version: str
    db_ok: bool
    sources: SourceReachability
    bricklink_budget_used: int = 0
    bricklink_budget_cap: int = 0
    bricklink_budget_remaining: int = 0


class TaskInfo(CamelModel):
    name: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class TasksEnvelope(CamelModel):
    records: List[TaskInfo] = []


class CommandRequest(CamelModel):
    name: str


class CommandAccepted(CamelModel):
    job_id: str
    name: str
    status: str = "queued"
