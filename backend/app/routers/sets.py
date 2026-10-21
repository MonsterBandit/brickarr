from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.db import get_db
from app.models.catalog import CatalogItem, ItemType
from app.models.owned import OwnedItem, OwnedCondition, OwnedStatus
from app.models.parts import PartItemType, SetPart
from app.schemas.base import PagedEnvelope
from app.schemas.parts import (
    MinifigLine,
    MinifigsEnvelope,
    OwnershipPatch,
    PartLine,
    PartsEnvelope,
)
from app.schemas.sets import (
    OwnedItemOut,
    SetCreate,
    SetDetail,
    SetLinks,
    SetLookupEnvelope,
    SetLookupRecord,
    SetPatch,
    SetStats,
    SetSummary,
)
from app.schemas.value import SetValue, ValueLinks
from app.services import brickset, buylist as buylist_service, catalog_mirror
from app.services.ownership import (
    derive,
    overrides_for_owned_item,
    resolve_set_part_id,
    rollup_totals,
    upsert_override,
)
from app.workers import jobs

router = APIRouter()


def _bricklink_link(set_number: str) -> str:
    return f"https://www.bricklink.com/v2/catalog/catalogitem.page?S={set_number}"


def _split_set_no(set_no: str) -> tuple[str, str]:
    if "-" in set_no:
        head, tail = set_no.rsplit("-", 1)
        return head, tail
    return set_no, "1"


def _detail_from(db: Session, owned: OwnedItem) -> SetDetail:
    ci = db.get(CatalogItem, (owned.item_type, owned.item_no))
    parts = db.query(SetPart).filter(SetPart.set_no == owned.item_no).all()
    overrides = overrides_for_owned_item(db, owned.id)
    om = derive(owned, parts, overrides)
    total_owned, total_missing = rollup_totals(om, parts)
    ppp: Optional[Decimal] = None
    if ci and ci.rrp and (ci.num_pieces or 0) > 0:
        ppp = (Decimal(ci.rrp) / Decimal(ci.num_pieces)).quantize(Decimal("0.0001"))
    return SetDetail(
        id=owned.id,
        set_number=owned.item_no,
        name=ci.name if ci else None,
        status=owned.status.value,
        condition=owned.condition.value if owned.condition else None,
        copies=owned.copies,
        storage_location=owned.storage_location,
        theme=ci.theme if ci else None,
        subtheme=ci.subtheme if ci else None,
        year=ci.year_released if ci else None,
        pieces=ci.num_pieces if ci else None,
        minifigs=ci.num_minifigs if ci else None,
        rrp=ci.rrp if ci else None,
        acquired_price=owned.acquired_price,
        acquired_date=owned.acquired_date,
        launch_date=ci.launch_date if ci else None,
        exit_date=ci.exit_date if ci else None,
        image_url=ci.image_url if ci else None,
        stats=SetStats(owned=total_owned, missing=total_missing, price_per_piece=ppp),
        current_value=None,
        gain_loss=None,
        links=SetLinks(bricklink=_bricklink_link(owned.item_no)),
    )


@router.get("/sets", response_model=PagedEnvelope[SetSummary])
def list_sets(
    status_q: Optional[str] = Query(default=None, alias="status"),
    theme: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_key: str = Query(default="name", alias="sortKey"),
    sort_direction: str = Query(default="ascending", alias="sortDirection"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500, alias="pageSize"),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    q = db.query(OwnedItem).filter(OwnedItem.item_type == ItemType.SET)
    if status_q:
        q = q.filter(OwnedItem.status == status_q)
    total = q.count()
    owned_rows = q.offset((page - 1) * page_size).limit(page_size).all()
    records: List[SetSummary] = []
    for o in owned_rows:
        ci = db.get(CatalogItem, (o.item_type, o.item_no))
        if theme and (not ci or ci.theme != theme):
            continue
        if search and ci and search.lower() not in (ci.name or "").lower():
            continue
        records.append(SetSummary(
            id=o.id,
            set_number=o.item_no,
            name=ci.name if ci else None,
            status=o.status.value,
            theme=ci.theme if ci else None,
            year=ci.year_released if ci else None,
            pieces=ci.num_pieces if ci else None,
            thumbnail_url=ci.thumbnail_url if ci else None,
            image_url=ci.image_url if ci else None,
        ))
    return PagedEnvelope[SetSummary](
        page=page,
        page_size=page_size,
        sort_key=sort_key,
        sort_direction=sort_direction,
        total_records=total,
        records=records,
    )


@router.get("/sets/lookup", response_model=SetLookupEnvelope)
def lookup_sets(
    term: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Brickset only until the Rebrickable catalogue arrives (BR.DK.09).
    try:
        brickset.get_api_key(db)
    except brickset.MissingCredentialsError:
        return SetLookupEnvelope(records=[], total_records=0,
                                 warning="No catalog sources configured")

    records: List[SetLookupRecord] = []
    try:
        for s in brickset.search_catalog(db, term):
            records.append(SetLookupRecord(
                item_type="SET",
                set_number=str(s.get("number") or s.get("setNumber") or term),
                name=s.get("name"),
                year=s.get("year"),
                theme=s.get("theme"),
                thumbnail_url=s.get("image", {}).get("thumbnailURL") if isinstance(s.get("image"), dict) else None,
                owned=False,
            ))
    except Exception:  # noqa: BLE001
        pass

    owned_numbers = {
        o.item_no for o in db.query(OwnedItem).filter(OwnedItem.item_type == ItemType.SET).all()
    }
    for r in records:
        r.owned = r.set_number in owned_numbers
    return SetLookupEnvelope(records=records, total_records=len(records))


@router.get("/sets/{owned_id}", response_model=SetDetail)
def get_set(owned_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    return _detail_from(db, owned)


@router.post("/sets", response_model=OwnedItemOut, status_code=status.HTTP_201_CREATED)
def create_set(
    body: SetCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    # Refuse before writing anything: there's no catalogue source until BR.DK.09.
    if not catalog_mirror.catalogue_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail={"error": "ServiceUnavailable",
                                    "message": catalog_mirror.CATALOGUE_UNAVAILABLE})
    set_no = body.set_number
    ci = db.get(CatalogItem, (ItemType.SET, set_no))
    if ci is None:
        ci = CatalogItem(item_type=ItemType.SET, item_no=set_no)
        db.add(ci)
        db.flush()
    try:
        owned_status = OwnedStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=[{"propertyName": "status",
                                                      "errorMessage": "Invalid status"}])
    condition = None
    if body.condition:
        try:
            condition = OwnedCondition(body.condition)
        except ValueError:
            raise HTTPException(status_code=400, detail=[{"propertyName": "condition",
                                                          "errorMessage": "Invalid condition"}])
    owned = OwnedItem(
        item_type=ItemType.SET,
        item_no=set_no,
        status=owned_status,
        copies=body.copies or 1,
        condition=condition,
        storage_location=body.storage_location,
        acquired_price=body.acquired_price,
        acquired_date=body.acquired_date,
        notes=body.notes,
    )
    db.add(owned)
    db.commit()

    job = jobs.enqueue(db, jobs.KIND_ADD_SET, f"Add set {set_no}")
    bg.add_task(jobs.add_set_job, set_no, job.id)
    return OwnedItemOut.model_validate(owned)


@router.patch("/sets/{owned_id}", response_model=OwnedItemOut)
def patch_set(owned_id: int, body: SetPatch, db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    if body.status is not None:
        try:
            owned.status = OwnedStatus(body.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=[{"propertyName": "status",
                                                          "errorMessage": "Invalid status"}])
    if body.condition is not None:
        owned.condition = OwnedCondition(body.condition) if body.condition else None
    if body.copies is not None:
        owned.copies = body.copies
    if body.storage_location is not None:
        owned.storage_location = body.storage_location
    if body.acquired_price is not None:
        owned.acquired_price = body.acquired_price
    if body.acquired_date is not None:
        owned.acquired_date = body.acquired_date
    if body.notes is not None:
        owned.notes = body.notes
    db.commit()
    return OwnedItemOut.model_validate(owned)


@router.delete("/sets/{owned_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(owned_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.get(OwnedItem, owned_id)
    if owned is not None:
        db.delete(owned)
        db.commit()
    return None


@router.get("/sets/{owned_id}/parts", response_model=PartsEnvelope)
def get_parts(
    owned_id: int,
    filter: Optional[str] = Query(default="all"),
    color_id: Optional[int] = Query(default=None, alias="colorId"),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    q = db.query(SetPart).filter(SetPart.set_no == owned.item_no)
    if color_id is not None:
        q = q.filter(SetPart.color_id == color_id)
    parts = q.all()
    overrides = overrides_for_owned_item(db, owned.id)
    om = derive(owned, parts, overrides)
    records: List[PartLine] = []
    for sp in parts:
        ci = db.get(CatalogItem, (ItemType(sp.part_item_type.value), sp.part_no))
        line = PartLine(
            set_part_id=sp.id,
            part_no=sp.part_no,
            part_item_type=sp.part_item_type.value,
            name=ci.name if ci else None,
            color_id=sp.color_id,
            color_name=None,
            thumbnail_url=ci.thumbnail_url if ci else None,
            quantity=sp.quantity,
            extra_quantity=sp.extra_quantity,
            owned=om[sp.id].owned,
            missing=om[sp.id].missing,
            is_alternate=sp.is_alternate,
            is_counterpart=sp.is_counterpart,
            match_no=sp.match_no,
        )
        if search and search.lower() not in ((line.name or "") + " " + line.part_no).lower():
            continue
        if filter == "owned" and line.owned == 0:
            continue
        if filter == "missing" and line.missing == 0:
            continue
        records.append(line)
    return PartsEnvelope(records=records)


@router.patch("/sets/{owned_id}/parts")
def patch_parts(
    owned_id: int,
    body: List[OwnershipPatch],
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    applied = 0
    for patch in body:
        sp_id = patch.set_part_id
        if sp_id is None:
            if patch.part_no is None or patch.color_id is None:
                continue
            sp_id = resolve_set_part_id(db, owned.item_no, patch.part_no, patch.color_id)
        if sp_id is None:
            continue
        upsert_override(db, owned.id, sp_id, patch.quantity_owned)
        applied += 1
    db.commit()
    return {"applied": applied}


@router.get("/sets/{owned_id}/minifigs", response_model=MinifigsEnvelope)
def get_minifigs(owned_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    parts = (
        db.query(SetPart)
        .filter(SetPart.set_no == owned.item_no, SetPart.part_item_type == PartItemType.MINIFIG)
        .all()
    )
    overrides = overrides_for_owned_item(db, owned.id)
    om = derive(owned, parts, overrides)
    records = []
    for sp in parts:
        ci = db.get(CatalogItem, (ItemType.MINIFIG, sp.part_no))
        records.append(MinifigLine(
            set_part_id=sp.id,
            part_no=sp.part_no,
            name=ci.name if ci else None,
            thumbnail_url=ci.thumbnail_url if ci else None,
            quantity=sp.quantity,
            owned=om[sp.id].owned,
            missing=om[sp.id].missing,
        ))
    return MinifigsEnvelope(records=records)


@router.get("/sets/{owned_id}/value", response_model=SetValue)
def get_value(owned_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    ci = db.get(CatalogItem, (owned.item_type, owned.item_no))
    head, tail = _split_set_no(owned.item_no)
    return SetValue(
        rrp=ci.rrp if ci else None,
        links=ValueLinks(
            price_guide=f"https://www.bricklink.com/catalogPG.asp?S={owned.item_no}",
            items_for_sale=f"https://www.bricklink.com/v2/catalog/catalogitem.page?S={owned.item_no}#T=S",
            part_out_value=f"https://www.bricklink.com/catalogPOV.asp?itemType=S&itemNo={head}&itemSeq={tail}",
        ),
        computed=None,
    )


@router.get("/sets/{owned_id}/buylist")
def get_buylist(
    owned_id: int,
    format: Optional[str] = Query(default="xml"),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    owned = db.get(OwnedItem, owned_id)
    if owned is None:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Set not found"})
    body, media_type = buylist_service.buylist_for_set(db, owned, format or "xml")
    return Response(content=body, media_type=media_type)
