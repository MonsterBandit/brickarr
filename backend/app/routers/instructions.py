from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.instruction import Instruction
from app.models.owned import OwnedItem
from app.schemas.instructions import (
    InstructionDownloadRequest,
    InstructionOut,
    InstructionsEnvelope,
)
from app.workers import jobs

router = APIRouter()


def _set_no_for_owned(db: Session, owned_id: int) -> str:
    row = db.get(OwnedItem, owned_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Owned set not found"})
    return row.item_no


@router.get("/sets/{owned_id}/instructions", response_model=InstructionsEnvelope)
def list_instructions(owned_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    set_no = _set_no_for_owned(db, owned_id)
    rows = db.query(Instruction).filter(Instruction.set_no == set_no).all()
    records = [
        InstructionOut(
            id=r.id,
            description=r.description,
            source_url=r.source_url,
            downloaded=r.downloaded_at is not None,
            local_path=r.local_path,
            size_bytes=r.file_size_bytes,
        )
        for r in rows
    ]
    return InstructionsEnvelope(records=records)


@router.post("/sets/{owned_id}/instructions/download", status_code=status.HTTP_202_ACCEPTED)
def download_instructions(
    owned_id: int,
    bg: BackgroundTasks,
    body: InstructionDownloadRequest | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    set_no = _set_no_for_owned(db, owned_id)
    ids = body.instruction_ids if body else None
    job = jobs.enqueue(db, jobs.KIND_DOWNLOAD_INSTRUCTIONS, f"Download instructions {set_no}")
    bg.add_task(jobs.download_instructions_job, set_no, ids, job.id)
    return {"jobId": job.id, "status": "queued"}


@router.get("/instructions/{instruction_id}/file")
def instruction_file(instruction_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(Instruction, instruction_id)
    if row is None or not row.local_path:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Instruction file not available"})
    p = Path(row.local_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "File missing on disk"})
    return FileResponse(p, media_type="application/pdf", filename=p.name)
