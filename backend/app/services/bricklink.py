from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote, urlencode

import httpx
from oauthlib.oauth1 import Client as OAuth1Client
from sqlalchemy.orm import Session

from app.crypto import decrypt_secret
from app.models.catalog import Color
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


class BrickLinkError(Exception):
    def __init__(self, code: int, message: Optional[str] = None, description: Optional[str] = None):
        self.code = code
        self.message = message or ""
        self.description = description or ""
        super().__init__(f"BrickLink {code}: {self.message}")


class NotFoundError(BrickLinkError):
    """404 RESOURCE_NOT_FOUND — e.g. unknown set number."""


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


def _build_url(path: str, params: Optional[dict]) -> str:
    url = f"{BRICKLINK_BASE}{path}"
    if not params:
        return url
    # RFC 3986 percent-encoding (spaces as %20, not '+') so oauthlib's signature
    # base string matches the URL httpx will transmit verbatim.
    qs = urlencode(params, quote_via=quote, safe="")
    return f"{url}?{qs}"


def _sign(c: Creds, method: str, url: str) -> tuple[str, dict, Optional[str]]:
    # Two-legged OAuth1 ("simpler flow"): the four static credentials are
    # everything; no token handshake. HMAC-SHA1, header-borne. The token is
    # bound to the server's registered outbound IP.
    client = OAuth1Client(
        c.consumer_key,
        client_secret=c.consumer_secret,
        resource_owner_key=c.token,
        resource_owner_secret=c.token_secret,
        signature_method="HMAC-SHA1",
        signature_type="auth_header",
    )
    uri, headers, body = client.sign(url, http_method=method)
    return uri, headers, body


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
    url = _build_url(path, params)
    uri, headers, _ = _sign(creds, method, url)
    with httpx.Client(timeout=timeout) as client:
        resp = client.request(method=method, url=uri, headers=headers, json=json_body)
    try:
        payload = resp.json()
    except ValueError:
        raise BrickLinkError(resp.status_code, "Non-JSON response", resp.text[:300])
    if isinstance(payload, dict) and "meta" in payload:
        meta = payload.get("meta") or {}
        try:
            code = int(meta.get("code") or 0)
        except (TypeError, ValueError):
            code = 0
        if 200 <= code < 300:
            return payload.get("data")
        if code == 404:
            raise NotFoundError(code, meta.get("message"), meta.get("description"))
        raise BrickLinkError(code, meta.get("message"), meta.get("description"))
    if resp.status_code >= 400:
        raise BrickLinkError(resp.status_code, "HTTP error", resp.text[:300])
    return payload


def get_catalog_item(db: Session, item_type: str, item_no: str) -> dict:
    return bricklink_call(db, "GET", f"/items/{item_type}/{item_no}")


def get_subsets(db: Session, item_type: str, item_no: str, break_minifigs: bool = False) -> list:
    # Returns a list of groups [{ "match_no": int, "entries": [...] }]. Each
    # entry has { "item": {"no","name","type","categoryID"}, "color_id",
    # "quantity", "extra_quantity", "is_alternate" }. No is_counterpart key
    # (that's an inventory concept on /supersets, not /subsets). Subset items
    # may be type PART | MINIFIG | INSTRUCTION | ORIGINAL_BOX | BOOK; callers
    # filter to PART/MINIFIG for the manifest.
    params = {"break_minifigs": "true" if break_minifigs else "false"}
    return bricklink_call(db, "GET", f"/items/{item_type}/{item_no}/subsets", params=params)


def get_colors(db: Session) -> list:
    # GET /colors returns the colour reference table. Each row carries
    # color_id, color_name, color_code (RGB hex, no '#'), color_type.
    return bricklink_call(db, "GET", "/colors")


def seed_colors(db: Session) -> int:
    rows = get_colors(db) or []
    n = 0
    for r in rows:
        cid = r.get("color_id")
        if cid is None:
            continue
        try:
            cid = int(cid)
        except (TypeError, ValueError):
            continue
        name = r.get("color_name")
        rgb = r.get("color_code")
        ctype = r.get("color_type")
        existing = db.get(Color, cid)
        if existing is None:
            db.add(Color(color_id=cid, name=name, rgb=rgb, type=ctype))
        else:
            if name:
                existing.name = name
            if rgb:
                existing.rgb = rgb
            if ctype:
                existing.type = ctype
        n += 1
    db.commit()
    return n


def search_catalog(db: Session, term: str) -> list:
    # BrickLink has no general search endpoint; the Add flow looks up by id.
    # If `term` looks like a set id (e.g. "43022-1") we try a direct fetch.
    try:
        item = get_catalog_item(db, "SET", term if "-" in term else f"{term}-1")
        return [item]
    except NotFoundError:
        return []
    except Exception:  # noqa: BLE001
        return []


def test_ping(db: Session) -> bool:
    # GET /colors is a stronger health check than fetching a single item — it
    # always exists, requires no specific catalog id, and the response is the
    # colour reference we need anyway. Doubles as the colour-table seed.
    try:
        seed_colors(db)
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
