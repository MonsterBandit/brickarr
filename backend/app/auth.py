from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, Query, Request, status
from itsdangerous import BadSignature, TimestampSigner
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.apikey import ApiKey
from app.models.setting import Setting

log = logging.getLogger(__name__)

SETTING_AUTH_MODE = "auth.mode"
SETTING_AUTH_USERNAME = "auth.username"
SETTING_AUTH_PASSWORD_HASH = "auth.password_hash"

AUTH_FORMS = "Forms"
AUTH_DISABLED_LOCAL = "DisabledForLocalAddresses"
AUTH_EXTERNAL = "External"


def _signer() -> TimestampSigner:
    return TimestampSigner(settings.session_secret)


def issue_session_token(username: str) -> str:
    return _signer().sign(username.encode("utf-8")).decode("ascii")


def verify_session_token(token: str) -> Optional[str]:
    try:
        raw = _signer().unsign(token.encode("ascii"), max_age=settings.session_max_age_seconds)
    except BadSignature:
        return None
    return raw.decode("utf-8")


def _api_key_pepper() -> bytes:
    p = settings.secret_key_path
    if not p.exists():
        return b""
    return p.read_bytes().strip()


def hash_api_key(plaintext: str) -> str:
    pepper = _api_key_pepper()
    return hashlib.sha256(pepper + plaintext.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def ensure_initial_api_key(db: Session) -> Optional[str]:
    existing = db.query(ApiKey).count()
    if existing > 0:
        return None
    plaintext = generate_api_key()
    row = ApiKey(
        name="default",
        key_hash=hash_api_key(plaintext),
        key_prefix=plaintext[:8],
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    out_path = settings.initial_api_key_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(plaintext + "\n")
    os.chmod(out_path, 0o600)
    log.warning("Brickarr first-run API key written to %s (mode 0600)", out_path)
    return plaintext


def _is_local(addr: Optional[str]) -> bool:
    if not addr:
        return False
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


def _get_auth_mode(db: Session) -> str:
    row = db.get(Setting, SETTING_AUTH_MODE)
    return (row.value if row and row.value else AUTH_FORMS) or AUTH_FORMS


def require_auth(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-Api-Key"),
    apikey_q: Optional[str] = Query(default=None, alias="apikey"),
    session_cookie: Optional[str] = Cookie(default=None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
) -> dict:
    presented = x_api_key or apikey_q
    if presented:
        h = hash_api_key(presented)
        row = db.query(ApiKey).filter(ApiKey.key_hash == h).first()
        if row:
            row.last_used_at = datetime.utcnow()
            db.commit()
            return {"principal": f"apikey:{row.name}"}

    if session_cookie:
        user = verify_session_token(session_cookie)
        if user:
            return {"principal": f"user:{user}"}

    mode = _get_auth_mode(db)
    if mode == AUTH_EXTERNAL:
        return {"principal": "external"}
    if mode == AUTH_DISABLED_LOCAL:
        client = request.client.host if request.client else None
        if _is_local(client):
            return {"principal": "local"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Unauthorized", "message": "Missing or invalid API key"},
    )


def _hash_password(pw: str, salt: bytes) -> str:
    return salt.hex() + ":" + hashlib.scrypt(pw.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32).hex()


def hash_password(pw: str) -> str:
    return _hash_password(pw, os.urandom(16))


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt_hex, _digest = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return hmac.compare_digest(_hash_password(pw, salt), stored)
