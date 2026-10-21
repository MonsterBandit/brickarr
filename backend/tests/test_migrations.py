from __future__ import annotations

import os
import sqlite3
from pathlib import Path

EXPECTED_TABLES = {
    "alembic_version", "api_key", "catalog_item", "color", "instruction", "job",
    "light_kit", "owned_item", "ownership", "price_cache", "set_part", "setting",
}


def _tables(db_file: Path) -> set[str]:
    with sqlite3.connect(db_file) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {r[0] for r in rows}


def test_upgrade_head_on_empty_sqlite_file(tmp_path, alembic_cli):
    env = os.environ.copy()
    env["BRICKARR_CONFIG_DIR"] = str(tmp_path)
    db_file = tmp_path / "brickarr.db"
    assert not db_file.exists()

    up = alembic_cli("upgrade", "head", env=env)
    assert up.returncode == 0, up.stderr
    assert _tables(db_file) == EXPECTED_TABLES

    # The models and the migration describe the same schema.
    check = alembic_cli("check", env=env)
    assert check.returncode == 0, check.stdout + check.stderr

    down = alembic_cli("downgrade", "base", env=env)
    assert down.returncode == 0, down.stderr
    assert _tables(db_file) == {"alembic_version"}

    again = alembic_cli("upgrade", "head", env=env)
    assert again.returncode == 0, again.stderr


def test_sqlite_foreign_keys_and_wal():
    from app.db import engine

    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert conn.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
