from __future__ import annotations

import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.crypto import decrypt_secret
from app.models.setting import Setting
from app.redis_client import get_redis

log = logging.getLogger(__name__)

BRICKSET_BASE = "https://brickset.com/api/v3.asmx"
REDIS_REACHABLE_KEY = "brickset:reachable"

SETTING_API_KEY = "brickset.api_key"
# userHash only populates the user-specific `collection` object on getSets;
# Brickarr tracks ownership itself, so we never need to send it.
SETTING_USER_HASH = "brickset.user_hash"


class MissingCredentialsError(Exception):
    pass


def _get_setting(db: Session, key: str) -> Optional[str]:
    row = db.get(Setting, key)
    if not row or row.value is None:
        return None
    return decrypt_secret(row.value) if row.is_secret else row.value


def get_api_key(db: Session) -> str:
    k = _get_setting(db, SETTING_API_KEY)
    if not k:
        raise MissingCredentialsError("Brickset API key not configured")
    return k


def brickset_call(db: Session, path: str, params: Optional[dict] = None, timeout: float = 20.0) -> dict:
    key = get_api_key(db)
    q = {"apiKey": key}
    if params:
        q.update(params)
    url = f"{BRICKSET_BASE}{path}"
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url, params=q)
    if resp.status_code >= 400:
        raise RuntimeError(f"Brickset {path} -> {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def get_set_by_number(db: Session, set_number: str) -> dict:
    # Brickset `params` is a stringified JSON object — Brickset quirk.
    return brickset_call(db, "/getSets", params={"params": f'{{"setNumber":"{set_number}"}}'})


def get_instructions(db: Session, set_id: str) -> list:
    # Keyed by setID (the numeric Brickset id from getSets), NOT the set
    # number. Entries carry the PDF link in `URL` (capitalised) plus
    # `description`. Links are plain lego.com CDN PDFs, unauthenticated GET.
    data = brickset_call(db, "/getInstructions", params={"setID": set_id})
    return data.get("instructions", []) if isinstance(data, dict) else []


def search_catalog(db: Session, term: str) -> list:
    try:
        data = brickset_call(db, "/getSets", params={"params": f'{{"query":"{term}","pageSize":20}}'})
        return data.get("sets", []) if isinstance(data, dict) else []
    except Exception:  # noqa: BLE001
        return []


def test_ping(db: Session) -> bool:
    try:
        brickset_call(db, "/checkKey")
        get_redis().setex(REDIS_REACHABLE_KEY, 24 * 3600, "1")
        return True
    except MissingCredentialsError:
        get_redis().setex(REDIS_REACHABLE_KEY, 300, "0")
        return False
    except Exception as exc:  # noqa: BLE001
        log.warning("Brickset test ping failed: %s", exc)
        get_redis().setex(REDIS_REACHABLE_KEY, 300, "0")
        return False


def last_reachable() -> Optional[bool]:
    val = get_redis().get(REDIS_REACHABLE_KEY)
    if val is None:
        return None
    return val == "1"
