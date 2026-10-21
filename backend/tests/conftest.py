"""Test setup: a throwaway SQLite database, migrated with Alembic.

Settings and the engine are built when app.config and app.db are first
imported, so the environment is set here at module level, before any test
module imports the app.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
_TMP = Path(tempfile.mkdtemp(prefix="brickarr-tests-"))

for _key in [k for k in os.environ if k.upper().startswith("BRICKARR_")]:
    del os.environ[_key]
os.environ.update({
    "BRICKARR_DB_TYPE": "sqlite",
    "BRICKARR_CONFIG_DIR": str(_TMP / "config"),
    "BRICKARR_LIBRARY_DIR": str(_TMP / "library"),
    "BRICKARR_VERSION": "0.0.0-test",
})
(_TMP / "config").mkdir()


def _run_alembic(*args: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run the alembic CLI from backend/, as the entrypoint does."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env if env is not None else os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def alembic_cli() -> Callable[..., subprocess.CompletedProcess]:
    return _run_alembic


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    result = _run_alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr
    yield
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(scope="session")
def client(migrated_db):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def api_headers(client) -> dict:
    # The lifespan writes the first-run key; reading it back proves the
    # api_key insert worked on SQLite.
    from app.config import settings

    return {"X-Api-Key": settings.initial_api_key_path.read_text().strip()}
