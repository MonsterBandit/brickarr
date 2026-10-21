from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.schemas.health import HealthItem
from app.services import brickset

router = APIRouter()


@router.get("/health", response_model=List[HealthItem])
def health(db: Session = Depends(get_db), _=Depends(require_auth)):
    items: List[HealthItem] = []
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        items.append(HealthItem(source="Database", type="error", message=f"DB unreachable: {exc}"))

    try:
        brickset.get_api_key(db)
        if brickset.last_reachable() is False:
            items.append(HealthItem(source="Brickset", type="warning",
                                    message="Brickset last test failed"))
    except brickset.MissingCredentialsError:
        items.append(HealthItem(source="Brickset", type="warning",
                                message="Brickset API key missing or invalid"))
    return items


@router.get("/ping")
def ping():
    return {"status": "ok"}
