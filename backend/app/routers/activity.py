from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.history import JobHistory
from app.schemas.activity import HistoryEnvelope, HistoryItem, QueueEnvelope, QueueItem
from app.workers import jobs

router = APIRouter()


@router.get("/queue", response_model=QueueEnvelope)
def get_queue(_=Depends(require_auth)):
    records = [QueueItem(**j) for j in jobs.list_active_jobs()]
    return QueueEnvelope(records=records)


@router.get("/history", response_model=HistoryEnvelope)
def get_history(
    event_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    q = db.query(JobHistory)
    if event_type:
        q = q.filter(JobHistory.event_type == event_type)
    total = q.count()
    rows = (
        q.order_by(JobHistory.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return HistoryEnvelope(
        page=page,
        page_size=page_size,
        total_records=total,
        records=[HistoryItem.model_validate(r) for r in rows],
    )
