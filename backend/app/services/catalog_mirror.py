from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem, ItemType
from app.models.instruction import Instruction
from app.models.parts import PartItemType, SetPart
from app.services import bricklink, brickset

log = logging.getLogger(__name__)

_PART_ITEM_TYPES = {"PART", "MINIFIG"}


def _ensure_catalog_row(db: Session, item_type: ItemType, item_no: str) -> CatalogItem:
    row = db.get(CatalogItem, (item_type, item_no))
    if row is None:
        row = CatalogItem(item_type=item_type, item_no=item_no)
        db.add(row)
        db.flush()
    return row


def _coerce_bool(v: Any) -> bool:
    # BrickLink returns is_alternate as a real JSON bool in practice but the
    # docs table labels it "String" — accept both shapes.
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() == "true"
    return bool(v)


def _ci_get(d: Optional[dict], key: str) -> Any:
    if not isinstance(d, dict):
        return None
    if key in d:
        return d[key]
    lower = key.lower()
    for k, v in d.items():
        if isinstance(k, str) and k.lower() == lower:
            return v
    return None


def mirror_catalog_set(db: Session, set_number: str) -> CatalogItem:
    data = bricklink.get_catalog_item(db, "SET", set_number)
    row = _ensure_catalog_row(db, ItemType.SET, set_number)
    row.name = data.get("name") or row.name
    # BrickLink live JSON sometimes serialises this as `categoryID`.
    row.category_id = data.get("category_id") or data.get("categoryID")
    row.year_released = data.get("year_released")
    row.image_url = data.get("image_url")
    row.thumbnail_url = data.get("thumbnail_url")
    row.weight_g = data.get("weight")
    row.dim_x_cm = data.get("dim_x")
    row.dim_y_cm = data.get("dim_y")
    row.dim_z_cm = data.get("dim_z")
    row.catalog_synced_at = datetime.utcnow()
    db.commit()
    return row


def mirror_subsets(db: Session, set_number: str) -> int:
    subsets = bricklink.get_subsets(db, "SET", set_number, break_minifigs=False)
    inserted = 0
    for group in subsets:
        match_no = int(group.get("match_no", 0) or 0)
        for entry in group.get("entries", []):
            item = entry.get("item") or {}
            part_type_raw = (item.get("type") or "PART").upper()
            # Subsets can include INSTRUCTION / ORIGINAL_BOX / BOOK rows; the
            # parts manifest is only PART and MINIFIG.
            if part_type_raw not in _PART_ITEM_TYPES:
                continue
            part_type = PartItemType.MINIFIG if part_type_raw == "MINIFIG" else PartItemType.PART
            part_no = item.get("no")
            if not part_no:
                continue
            color_id = int(entry.get("color_id", 0) or 0)
            _ensure_catalog_row(db, ItemType[part_type.value], part_no)
            sp = SetPart(
                set_no=set_number,
                part_item_type=part_type,
                part_no=part_no,
                color_id=color_id,
                quantity=int(entry.get("quantity", 0) or 0),
                extra_quantity=int(entry.get("extra_quantity", 0) or 0),
                is_alternate=_coerce_bool(entry.get("is_alternate", False)),
                # No is_counterpart flag on /subsets entries — that's an
                # inventory concept exposed via /supersets. Default false.
                is_counterpart=_coerce_bool(entry.get("is_counterpart", False)),
                match_no=match_no,
            )
            db.add(sp)
            inserted += 1
    db.commit()
    return inserted


def _select_brickset_entry(sets: list, set_number: str) -> Optional[dict]:
    # Brickset's `number` excludes the variant; the BrickLink-style key is
    # `f"{number}-{numberVariant}"`. Find the matching entry by composed key,
    # fall back to the first record if Brickset only returned one.
    for s in sets:
        n = s.get("number")
        v = s.get("numberVariant")
        if n is not None and v is not None and f"{n}-{v}" == set_number:
            return s
    return sets[0] if sets else None


def enrich_from_brickset(db: Session, set_number: str) -> Optional[CatalogItem]:
    try:
        data = brickset.get_set_by_number(db, set_number)
    except brickset.MissingCredentialsError:
        return None
    sets = data.get("sets", []) if isinstance(data, dict) else []
    s = _select_brickset_entry(sets, set_number)
    if s is None:
        return None
    row = db.get(CatalogItem, (ItemType.SET, set_number))
    if row is None:
        return None
    row.theme = s.get("theme") or row.theme
    row.subtheme = s.get("subtheme") or row.subtheme

    # Retail price is nested under LEGOCom.<country>.retailPrice. Older samples
    # capitalise the key as RetailPrice; look it up case-insensitively.
    legocom = s.get("LEGOCom") or s.get("legoCom") or {}
    us = _ci_get(legocom, "US") or {}
    row.rrp = _ci_get(us, "retailPrice") or row.rrp

    # Age range is nested, not flat ageMin/ageMax.
    age_range = s.get("ageRange") or {}
    row.age_min = age_range.get("min") or row.age_min
    row.age_max = age_range.get("max") or row.age_max

    row.launch_date = s.get("launchDate") or row.launch_date
    row.exit_date = s.get("exitDate") or row.exit_date
    row.num_pieces = s.get("pieces") or row.num_pieces
    row.num_minifigs = s.get("minifigs") or row.num_minifigs
    row.rating = s.get("rating") or row.rating

    # Thumbnail is nested under `image.thumbnailURL`.
    image = s.get("image") or {}
    row.thumbnail_url = image.get("thumbnailURL") or row.thumbnail_url

    row.brickset_id = str(s.get("setID")) if s.get("setID") is not None else row.brickset_id
    row.brickset_synced_at = datetime.utcnow()

    # Instructions are keyed by setID (not set number). Without it there is no
    # instructions call.
    if row.brickset_id:
        try:
            booklets = brickset.get_instructions(db, row.brickset_id)
        except Exception:  # noqa: BLE001
            booklets = []
        for b in booklets:
            url = b.get("URL") or b.get("url") or b.get("sourceURL")
            desc = b.get("description") or "Instruction booklet"
            if not url:
                continue
            existing = (
                db.query(Instruction)
                .filter(Instruction.set_no == set_number, Instruction.source_url == url)
                .first()
            )
            if existing:
                continue
            db.add(Instruction(set_no=set_number, description=desc, source_url=url))
    db.commit()
    return row
