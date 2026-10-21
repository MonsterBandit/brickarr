from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models.instruction import Instruction
from app.models.job import Job
from app.services import catalog_mirror

log = logging.getLogger(__name__)

QUEUED = "queued"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
ACTIVE = (QUEUED, RUNNING)
FINISHED = (COMPLETED, FAILED)

KIND_ADD_SET = "add_set"
KIND_DOWNLOAD_INSTRUCTIONS = "download_instructions"
KIND_COMMAND = "command"

# A download writes its progress at most this often, not once per 64 KB chunk.
PROGRESS_INTERVAL_SECONDS = 1.0


def enqueue(db: Session, kind: str, name: str, total: int = 0) -> Job:
    """Record a queued job from the request, before its background task runs."""
    job = Job(name=name, kind=kind, status=QUEUED, progress=0, total=total, created_at=datetime.utcnow())
    db.add(job)
    db.commit()
    return job


def _job(db: Session, job_id: int) -> Optional[Job]:
    job = db.get(Job, job_id)
    if job is None:
        log.warning("Job %s vanished from the job table", job_id)
    return job


def start_job(db: Session, job_id: int, total: Optional[int] = None) -> None:
    job = _job(db, job_id)
    if job is None:
        return
    job.status = RUNNING
    job.started_at = datetime.utcnow()
    if total is not None:
        job.total = total
    db.commit()


def update_progress(db: Session, job_id: int, progress: int, total: Optional[int] = None) -> None:
    job = _job(db, job_id)
    if job is None:
        return
    job.progress = progress
    if total is not None:
        job.total = total
    db.commit()


def finish_job(db: Session, job_id: int, status: str, message: str = "") -> None:
    job = _job(db, job_id)
    if job is None:
        return
    job.status = status
    job.message = message or None
    job.finished_at = datetime.utcnow()
    db.commit()


def add_set_job(set_number: str, job_id: int) -> None:
    db = SessionLocal()
    try:
        start_job(db, job_id, total=1)
        # BR.DK.09 adds the catalogue and parts-list steps (Rebrickable) here.
        catalog_mirror.enrich_from_brickset(db, set_number)
        update_progress(db, job_id, 1)
        finish_job(db, job_id, COMPLETED)
    except Exception as exc:  # noqa: BLE001
        log.exception("add_set_job failed for %s", set_number)
        db.rollback()
        finish_job(db, job_id, FAILED, str(exc))
    finally:
        db.close()


def _set_dir(set_no: str) -> Path:
    # Official booklets can be fetched again, so they go to the cache (BRK-15).
    p = settings.cache_dir / "instructions" / set_no
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_instructions_job(set_no: str, instruction_ids: Optional[Iterable[int]], job_id: int) -> None:
    db = SessionLocal()
    try:
        start_job(db, job_id)
        q = db.query(Instruction).filter(Instruction.set_no == set_no)
        if instruction_ids:
            q = q.filter(Instruction.id.in_(list(instruction_ids)))
        booklets = q.all()
        if not booklets:
            finish_job(db, job_id, COMPLETED, "No instructions to download")
            return
        progress = 0
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            sizes: list[int] = []
            for b in booklets:
                if not b.source_url:
                    sizes.append(0)
                    continue
                try:
                    head = client.head(b.source_url)
                    sizes.append(int(head.headers.get("content-length", 0) or 0))
                except Exception:  # noqa: BLE001
                    sizes.append(0)
            update_progress(db, job_id, 0, sum(sizes))
            last_write = time.monotonic()
            for b in booklets:
                if not b.source_url:
                    continue
                fname = f"{b.id}-{(b.description or 'booklet').replace('/', '_')}.pdf"
                dest = _set_dir(set_no) / fname
                tmp = dest.with_suffix(dest.suffix + ".part")
                bytes_written = 0
                with client.stream("GET", b.source_url) as resp:
                    resp.raise_for_status()
                    with open(tmp, "wb") as fh:
                        for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                            if not chunk:
                                continue
                            fh.write(chunk)
                            bytes_written += len(chunk)
                            progress += len(chunk)
                            now = time.monotonic()
                            if now - last_write >= PROGRESS_INTERVAL_SECONDS:
                                update_progress(db, job_id, progress)
                                last_write = now
                os.replace(tmp, dest)
                b.local_path = str(dest)
                b.file_size_bytes = bytes_written
                b.downloaded_at = datetime.utcnow()
                db.commit()
        update_progress(db, job_id, progress)
        finish_job(db, job_id, COMPLETED)
    except Exception as exc:  # noqa: BLE001
        log.exception("download_instructions_job failed for %s", set_no)
        db.rollback()
        finish_job(db, job_id, FAILED, str(exc))
    finally:
        db.close()


def command_job(command_name: str, job_id: int) -> None:
    db = SessionLocal()
    try:
        start_job(db, job_id)
        finish_job(db, job_id, COMPLETED, f"{command_name} no-op (alpha)")
    finally:
        db.close()
