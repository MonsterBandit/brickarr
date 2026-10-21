from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.job import Job
from app.schemas.activity import HistoryEnvelope, HistoryItem, QueueEnvelope, QueueItem
from app.workers import jobs

router = APIRouter()


@router.get("/queue", response_model=QueueEnvelope)
def get_queue(db: Session = Depends(get_db), _=Depends(require_auth)):
    rows = db.query(Job).filter(Job.status.in_(jobs.ACTIVE)).order_by(Job.id.asc()).all()
    return QueueEnvelope(records=[QueueItem.model_validate(r) for r in rows])


@router.get("/history", response_model=HistoryEnvelope)
def get_history(
    kind: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500, alias="pageSize"),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    q = db.query(Job).filter(Job.status.in_(jobs.FINISHED))
    if kind:
        q = q.filter(Job.kind == kind)
    total = q.count()
    rows = (
        q.order_by(Job.finished_at.desc(), Job.id.desc())
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
