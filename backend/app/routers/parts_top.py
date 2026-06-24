from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.schemas.parts import PartPrice

router = APIRouter()


@router.get("/parts/{part_no}/price", response_model=PartPrice)
def part_price(
    part_no: str,
    color_id: Optional[int] = Query(default=None, alias="colorId"),
    guide_type: Optional[str] = Query(default=None, alias="guideType"),
    condition: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Pricing is link-out only in alpha; no DB cache populated, no BrickLink call made.
    return PartPrice(available=False, part_no=part_no, color_id=color_id,
                     guide_type=guide_type, condition=condition)
