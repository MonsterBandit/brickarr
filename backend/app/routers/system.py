from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.config import settings
from app.db import get_db
from app.schemas.system import (
    CommandAccepted,
    CommandRequest,
    SourceReachability,
    SystemStatus,
    TaskInfo,
    TasksEnvelope,
)
from app.services import brickset
from app.workers import jobs

router = APIRouter()

ALLOWED_COMMANDS = {
    "RefreshManifests",
    "RefreshPrices",
    "CheckRetirements",
    "CheckPriceDrops",
    "SyncImportLists",
}

TASK_NAMES = [
    "refresh-prices",
    "check-retirements",
    "check-price-drops",
    "sync-import-lists",
    "refresh-manifests",
]


@router.get("/system/status", response_model=SystemStatus)
def system_status(db: Session = Depends(get_db), _=Depends(require_auth)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    return SystemStatus(
        version=settings.version,
        db_type=settings.db_type,
        db_ok=db_ok,
        sources=SourceReachability(brickset=brickset.last_reachable()),
    )


@router.get("/system/tasks", response_model=TasksEnvelope)
def system_tasks(_=Depends(require_auth)):
    return TasksEnvelope(records=[TaskInfo(name=n, last_run_at=None, next_run_at=None) for n in TASK_NAMES])


@router.post("/command", response_model=CommandAccepted, status_code=status.HTTP_202_ACCEPTED)
def post_command(
    body: CommandRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    if body.name not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=400, detail=[{"propertyName": "name",
                                                      "errorMessage": f"Unknown command '{body.name}'"}])
    job = jobs.enqueue(db, jobs.KIND_COMMAND, body.name)
    bg.add_task(jobs.command_job, body.name, job.id)
    return CommandAccepted(job_id=job.id, name=body.name)
