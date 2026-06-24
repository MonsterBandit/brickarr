from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.catalog import CatalogItem, ItemType
from app.models.owned import OwnedItem
from app.schemas.collection import CollectionCounts, CollectionValue
from app.services import buylist as buylist_service

router = APIRouter()


@router.get("/collection/value", response_model=CollectionValue)
def collection_value(db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.query(OwnedItem).all()
    set_count = sum(1 for o in owned if o.item_type == ItemType.SET)
    rrp_total: Decimal = Decimal("0")
    acquired_total: Decimal = Decimal("0")
    for o in owned:
        if o.acquired_price is not None:
            acquired_total += Decimal(o.acquired_price)
        ci = db.get(CatalogItem, (o.item_type, o.item_no))
        if ci and ci.rrp is not None:
            rrp_total += Decimal(ci.rrp)
    return CollectionValue(
        counts=CollectionCounts(sets=set_count, minifigs=0, parts=0),
        rrp_total=rrp_total if rrp_total > 0 else None,
        acquired_total=acquired_total if acquired_total > 0 else None,
        current_value_total=None,
        gain_loss_total=None,
    )


@router.get("/buylist")
def collection_buylist(
    format: Optional[str] = Query(default="xml"),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    owned = db.query(OwnedItem).filter(OwnedItem.item_type == ItemType.SET).all()
    body, media_type = buylist_service.buylist_for_collection(db, owned, format or "xml")
    return Response(content=body, media_type=media_type)
