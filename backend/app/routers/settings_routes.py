from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import generate_api_key, hash_api_key, require_auth
from app.crypto import encrypt_secret
from app.db import get_db
from app.models.apikey import ApiKey
from app.models.setting import Setting
from app.schemas.settings import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyList,
    ApiKeyOut,
    SettingOut,
    SettingWrite,
)

router = APIRouter()


@router.get("/settings", response_model=List[SettingOut])
def list_settings(db: Session = Depends(get_db), _=Depends(require_auth)):
    rows = db.query(Setting).all()
    out: List[SettingOut] = []
    for r in rows:
        if r.is_secret:
            out.append(SettingOut(key=r.key, value=None, is_secret=True))
        else:
            out.append(SettingOut(key=r.key, value=r.value, is_secret=False))
    return out


@router.get("/settings/{key}", response_model=SettingOut)
def get_setting(key: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(Setting, key)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Setting not found"})
    if row.is_secret:
        return SettingOut(key=row.key, value=None, is_secret=True)
    return SettingOut(key=row.key, value=row.value, is_secret=False)


@router.put("/settings/{key}", response_model=SettingOut)
def put_setting(key: str, body: SettingWrite, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(Setting, key)
    stored_value = body.value
    if body.is_secret and stored_value is not None:
        stored_value = encrypt_secret(stored_value)
    if row is None:
        row = Setting(key=key, value=stored_value, is_secret=body.is_secret)
        db.add(row)
    else:
        row.value = stored_value
        row.is_secret = body.is_secret
    db.commit()
    return SettingOut(key=row.key, value=None if row.is_secret else row.value, is_secret=row.is_secret)


@router.delete("/settings/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setting(key: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(Setting, key)
    if row is not None:
        db.delete(row)
        db.commit()
    return None


@router.get("/apikeys", response_model=ApiKeyList)
def list_apikeys(db: Session = Depends(get_db), _=Depends(require_auth)):
    rows = db.query(ApiKey).order_by(ApiKey.id.asc()).all()
    return ApiKeyList(records=[ApiKeyOut.model_validate(r) for r in rows])


@router.post("/apikeys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_apikey(body: ApiKeyCreate, db: Session = Depends(get_db), _=Depends(require_auth)):
    plaintext = generate_api_key()
    row = ApiKey(
        name=body.name,
        key_hash=hash_api_key(plaintext),
        key_prefix=plaintext[:8],
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return ApiKeyCreated(id=row.id, name=row.name, key=plaintext, key_prefix=row.key_prefix)


@router.delete("/apikeys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_apikey(key_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    row = db.get(ApiKey, key_id)
    if row is not None:
        db.delete(row)
        db.commit()
    return None
