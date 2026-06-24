from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from requests_oauthlib import OAuth1
from sqlalchemy.orm import Session

from app.crypto import decrypt_secret
from app.models.setting import Setting
from app.redis_client import BudgetExhaustedError, consume_budget, get_redis

log = logging.getLogger(__name__)

BRICKLINK_BASE = "https://api.bricklink.com/api/store/v1"
REDIS_REACHABLE_KEY = "bricklink:reachable"

SETTING_CONSUMER_KEY = "bricklink.consumer_key"
SETTING_CONSUMER_SECRET = "bricklink.consumer_secret"
SETTING_TOKEN = "bricklink.token"
SETTING_TOKEN_SECRET = "bricklink.token_secret"
SETTING_DAILY_CAP = "bricklink.daily_cap"
DEFAULT_DAILY_CAP = 5000


class MissingCredentialsError(Exception):
    pass


@dataclass
class Creds:
    consumer_key: str
    consumer_secret: str
    token: str
    token_secret: str


def _get_setting(db: Session, key: str) -> Optional[str]:
    row = db.get(Setting, key)
    if not row or row.value is None:
        return None
    return decrypt_secret(row.value) if row.is_secret else row.value


def get_credentials(db: Session) -> Creds:
    ck = _get_setting(db, SETTING_CONSUMER_KEY)
    cs = _get_setting(db, SETTING_CONSUMER_SECRET)
    tk = _get_setting(db, SETTING_TOKEN)
    ts = _get_setting(db, SETTING_TOKEN_SECRET)
    if not (ck and cs and tk and ts):
        raise MissingCredentialsError("BrickLink credentials not configured")
    return Creds(ck, cs, tk, ts)


def get_daily_cap(db: Session) -> int:
    row = db.get(Setting, SETTING_DAILY_CAP)
    if row and row.value:
        try:
            return max(int(row.value), 0)
        except ValueError:
            pass
    return DEFAULT_DAILY_CAP


def _auth(c: Creds) -> OAuth1:
    # TODO(report:001) OAuth1 signature edge cases (query encoding, body inclusion)
    return OAuth1(c.consumer_key, c.consumer_secret, c.token, c.token_secret, signature_type="auth_header")


def bricklink_call(
    db: Session,
    method: str,
    path: str,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    timeout: float = 20.0,
) -> Any:
    cap = get_daily_cap(db)
    consume_budget(cap, n=1)
    creds = get_credentials(db)
    url = f"{BRICKLINK_BASE}{path}"
    # requests_oauthlib produces a callable auth object that httpx accepts via custom auth flow
    # but its API is requests-style. We sign manually with requests then transplant headers.
    import requests as _requests
    req = _requests.Request(method=method, url=url, params=params, json=json_body)
    prepared = req.prepare()
    auth = _auth(creds)
    auth(prepared)
    with httpx.Client(timeout=timeout) as client:
        resp = client.request(
            method=method,
            url=str(prepared.url),
            headers=dict(prepared.headers),
            json=json_body,
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"BrickLink {method} {path} -> {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    # TODO(report:001) confirmed envelope shape: {"meta": {...}, "data": ...}
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def get_catalog_item(db: Session, item_type: str, item_no: str) -> dict:
    return bricklink_call(db, "GET", f"/items/{item_type}/{item_no}")


def get_subsets(db: Session, item_type: str, item_no: str, break_minifigs: bool = False) -> list:
    # TODO(report:002) Subsets response: list of entries with "entries" each containing items
    params = {"break_minifigs": "true" if break_minifigs else "false"}
    return bricklink_call(db, "GET", f"/items/{item_type}/{item_no}/subsets", params=params)


def search_catalog(db: Session, term: str) -> list:
    # BrickLink has no general search endpoint; the Add flow looks up by id.
    # If `term` looks like a set id (e.g. "43022-1") we try a direct fetch.
    try:
        item = get_catalog_item(db, "SET", term if "-" in term else f"{term}-1")
        return [item]
    except Exception:  # noqa: BLE001
        return []


def test_ping(db: Session) -> bool:
    try:
        get_catalog_item(db, "SET", "1-1")
        get_redis().setex(REDIS_REACHABLE_KEY, 24 * 3600, "1")
        return True
    except (MissingCredentialsError, BudgetExhaustedError):
        get_redis().setex(REDIS_REACHABLE_KEY, 300, "0")
        return False
    except Exception as exc:  # noqa: BLE001
        log.warning("BrickLink test ping failed: %s", exc)
        get_redis().setex(REDIS_REACHABLE_KEY, 300, "0")
        return False


def last_reachable() -> Optional[bool]:
    val = get_redis().get(REDIS_REACHABLE_KEY)
    if val is None:
        return None
    return val == "1"
