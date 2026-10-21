from __future__ import annotations

from app.db import SessionLocal
from app.workers import jobs


def test_job_row_is_read_through_queue(client, api_headers):
    with SessionLocal() as db:
        job = jobs.enqueue(db, "test", "Test job", total=10)
        jobs.start_job(db, job.id)
        jobs.update_progress(db, job.id, 4)
        job_id = job.id

    r = client.get("/api/v1/queue", headers=api_headers)
    assert r.status_code == 200
    rec = next(x for x in r.json()["records"] if x["id"] == job_id)
    assert rec["name"] == "Test job"
    assert rec["kind"] == "test"
    assert rec["status"] == "running"
    assert (rec["progress"], rec["total"]) == (4, 10)
    assert rec["startedAt"]

    with SessionLocal() as db:
        jobs.finish_job(db, job_id, jobs.COMPLETED)
    r = client.get("/api/v1/queue", headers=api_headers)
    assert all(x["id"] != job_id for x in r.json()["records"])


def test_command_job_lands_in_history(client, api_headers):
    r = client.post("/api/v1/command", json={"name": "RefreshManifests"}, headers=api_headers)
    assert r.status_code == 202
    job_id = r.json()["jobId"]

    r = client.get("/api/v1/history", params={"kind": jobs.KIND_COMMAND}, headers=api_headers)
    assert r.status_code == 200
    rec = next(x for x in r.json()["records"] if x["id"] == job_id)
    assert rec["status"] == "completed"
    assert rec["finishedAt"]
