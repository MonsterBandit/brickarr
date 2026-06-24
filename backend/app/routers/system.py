from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.redis_client import get_budget_remaining, get_budget_used
from app.schemas.system import (
    CommandAccepted,
    CommandRequest,
    SourceReachability,
    SystemStatus,
    TaskInfo,
    TasksEnvelope,
)
from app.services import bricklink, brickset
from app.workers import jobs

router = APIRouter()

VERSION = "0.1.0-alpha.1"

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
    cap = bricklink.get_daily_cap(db)
    used = get_budget_used()
    remaining = get_budget_remaining(cap)
    return SystemStatus(
        version=VERSION,
        db_ok=db_ok,
        sources=SourceReachability(
            bricklink=bricklink.last_reachable(),
            brickset=brickset.last_reachable(),
        ),
        bricklink_budget_used=used,
        bricklink_budget_cap=cap,
        bricklink_budget_remaining=remaining,
    )


@router.get("/system/tasks", response_model=TasksEnvelope)
def system_tasks(_=Depends(require_auth)):
    return TasksEnvelope(records=[TaskInfo(name=n, last_run_at=None, next_run_at=None) for n in TASK_NAMES])


@router.post("/command", response_model=CommandAccepted, status_code=status.HTTP_202_ACCEPTED)
def post_command(body: CommandRequest, bg: BackgroundTasks, _=Depends(require_auth)):
    if body.name not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=400, detail=[{"propertyName": "name",
                                                      "errorMessage": f"Unknown command '{body.name}'"}])
    job_id = jobs.new_job_id()
    bg.add_task(jobs.command_job, body.name, job_id)
    return CommandAccepted(job_id=job_id, name=body.name)
