from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem, ItemType
from app.models.instruction import Instruction
from app.services import brickset

log = logging.getLogger(__name__)

# The BrickLink client is gone (BRK-31). Set details and parts lists come from
# Rebrickable in BR.DK.09; until then adding a set is refused with this message.
CATALOGUE_UNAVAILABLE = "Catalogue source arrives in BR.DK.09"


def catalogue_available() -> bool:
    return False


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
