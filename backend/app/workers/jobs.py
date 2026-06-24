from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import httpx

from app.config import settings
from app.db import SessionLocal
from app.models.history import JobHistory
from app.models.instruction import Instruction
from app.redis_client import get_redis
from app.services import catalog_mirror

log = logging.getLogger(__name__)

JOB_KEY_PREFIX = "job:"
JOB_INDEX_KEY = "jobs:active"


def new_job_id() -> str:
    return secrets.token_hex(8)


def _job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


def init_job(job_id: str, name: str, total_bytes: int = 0) -> None:
    r = get_redis()
    r.hset(
        _job_key(job_id),
        mapping={
            "status": "queued",
            "name": name,
            "progress_bytes": 0,
            "total_bytes": total_bytes,
            "error": "",
            "started_at": datetime.utcnow().isoformat(),
        },
    )
    r.sadd(JOB_INDEX_KEY, job_id)
    r.expire(_job_key(job_id), 24 * 3600)


def update_progress(job_id: str, progress_bytes: int, total_bytes: Optional[int] = None) -> None:
    r = get_redis()
    mapping = {"status": "running", "progress_bytes": progress_bytes}
    if total_bytes is not None:
        mapping["total_bytes"] = total_bytes
    r.hset(_job_key(job_id), mapping=mapping)


def finish_job(job_id: str, status: str, message: str = "", event_type: str = "job", name: str = "") -> None:
    r = get_redis()
    r.hset(_job_key(job_id), mapping={"status": status, "error": message})
    r.srem(JOB_INDEX_KEY, job_id)
    db = SessionLocal()
    try:
        existing = db.query(JobHistory).filter(JobHistory.job_id == job_id).first()
        if existing:
            existing.status = status
            existing.message = message
            existing.finished_at = datetime.utcnow()
        else:
            db.add(
                JobHistory(
                    job_id=job_id,
                    event_type=event_type,
                    name=name,
                    status=status,
                    message=message,
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                )
            )
        db.commit()
    finally:
        db.close()


def list_active_jobs() -> List[dict]:
    r = get_redis()
    out: List[dict] = []
    ids = r.smembers(JOB_INDEX_KEY) or set()
    for jid in ids:
        data = r.hgetall(_job_key(jid)) or {}
        if not data:
            r.srem(JOB_INDEX_KEY, jid)
            continue
        out.append({
            "job_id": jid,
            "name": data.get("name"),
            "status": data.get("status", "unknown"),
            "progress_bytes": int(data.get("progress_bytes", 0) or 0),
            "total_bytes": int(data.get("total_bytes", 0) or 0),
            "error": data.get("error") or None,
        })
    return out


def add_set_job(set_number: str, job_id: str) -> None:
    init_job(job_id, name=f"Add set {set_number}")
    db = SessionLocal()
    try:
        update_progress(job_id, 0, 3)
        catalog_mirror.mirror_catalog_set(db, set_number)
        update_progress(job_id, 1, 3)
        catalog_mirror.mirror_subsets(db, set_number)
        update_progress(job_id, 2, 3)
        catalog_mirror.enrich_from_brickset(db, set_number)
        update_progress(job_id, 3, 3)
        finish_job(job_id, status="completed", event_type="add_set", name=f"Add set {set_number}")
    except Exception as exc:  # noqa: BLE001
        log.exception("add_set_job failed for %s", set_number)
        finish_job(job_id, status="failed", message=str(exc), event_type="add_set", name=f"Add set {set_number}")
    finally:
        db.close()


def _set_dir(set_no: str) -> Path:
    p = settings.storage_dir / "instructions" / set_no
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_instructions_job(set_no: str, instruction_ids: Optional[Iterable[int]], job_id: str) -> None:
    init_job(job_id, name=f"Download instructions {set_no}")
    db = SessionLocal()
    try:
        q = db.query(Instruction).filter(Instruction.set_no == set_no)
        if instruction_ids:
            q = q.filter(Instruction.id.in_(list(instruction_ids)))
        booklets = q.all()
        if not booklets:
            finish_job(job_id, status="completed", message="No instructions to download",
                       event_type="download_instructions", name=f"Download instructions {set_no}")
            return
        total_bytes = 0
        progress = 0
        update_progress(job_id, 0, 0)
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
            total_bytes = sum(sizes)
            update_progress(job_id, 0, total_bytes)
            for b, declared_size in zip(booklets, sizes):
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
                            update_progress(job_id, progress, total_bytes)
                os.replace(tmp, dest)
                b.local_path = str(dest)
                b.file_size_bytes = bytes_written
                b.downloaded_at = datetime.utcnow()
                db.commit()
        finish_job(job_id, status="completed", event_type="download_instructions",
                   name=f"Download instructions {set_no}")
    except Exception as exc:  # noqa: BLE001
        log.exception("download_instructions_job failed for %s", set_no)
        finish_job(job_id, status="failed", message=str(exc),
                   event_type="download_instructions", name=f"Download instructions {set_no}")
    finally:
        db.close()


def command_job(command_name: str, job_id: str) -> None:
    init_job(job_id, name=command_name)
    finish_job(job_id, status="completed",
               message=f"{command_name} no-op (alpha)",
               event_type="command", name=command_name)
