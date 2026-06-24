from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem, ItemType
from app.models.instruction import Instruction
from app.models.parts import PartItemType, SetPart
from app.services import bricklink, brickset

log = logging.getLogger(__name__)


def _ensure_catalog_row(db: Session, item_type: ItemType, item_no: str) -> CatalogItem:
    row = db.get(CatalogItem, (item_type, item_no))
    if row is None:
        row = CatalogItem(item_type=item_type, item_no=item_no)
        db.add(row)
        db.flush()
    return row


def mirror_catalog_set(db: Session, set_number: str) -> CatalogItem:
    # TODO(report:001) confirm BrickLink catalog item fields used here
    data = bricklink.get_catalog_item(db, "SET", set_number)
    row = _ensure_catalog_row(db, ItemType.SET, set_number)
    row.name = data.get("name") or row.name
    row.category_id = data.get("category_id")
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
    # TODO(report:002) Subsets shape: list[{match_no, entries:[{item:{type,no}, color_id, quantity, extra_quantity, is_alternate, is_counterpart}]}]
    subsets = bricklink.get_subsets(db, "SET", set_number, break_minifigs=False)
    inserted = 0
    for group in subsets:
        match_no = int(group.get("match_no", 0) or 0)
        for entry in group.get("entries", []):
            item = entry.get("item") or {}
            part_type_raw = (item.get("type") or "PART").upper()
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
                is_alternate=bool(entry.get("is_alternate", False)),
                is_counterpart=bool(entry.get("is_counterpart", False)),
                match_no=match_no,
            )
            db.add(sp)
            inserted += 1
    db.commit()
    return inserted


def enrich_from_brickset(db: Session, set_number: str) -> Optional[CatalogItem]:
    # TODO(report:003) Brickset getSets field names: theme, subtheme, rrp/USretailPrice, launchDate, exitDate
    try:
        data = brickset.get_set_by_number(db, set_number)
    except brickset.MissingCredentialsError:
        return None
    sets = data.get("sets", []) if isinstance(data, dict) else []
    if not sets:
        return None
    s = sets[0]
    row = db.get(CatalogItem, (ItemType.SET, set_number))
    if row is None:
        return None
    row.theme = s.get("theme") or row.theme
    row.subtheme = s.get("subtheme") or row.subtheme
    row.rrp = s.get("USretailPrice") or row.rrp
    row.launch_date = s.get("launchDate") or row.launch_date
    row.exit_date = s.get("exitDate") or row.exit_date
    row.age_min = s.get("ageMin") or row.age_min
    row.age_max = s.get("ageMax") or row.age_max
    row.num_pieces = s.get("pieces") or row.num_pieces
    row.num_minifigs = s.get("minifigs") or row.num_minifigs
    row.rating = s.get("rating") or row.rating
    row.brickset_id = str(s.get("setID")) if s.get("setID") is not None else row.brickset_id
    row.brickset_synced_at = datetime.utcnow()

    if row.brickset_id:
        try:
            booklets = brickset.get_instructions(db, row.brickset_id)
        except Exception:  # noqa: BLE001
            booklets = []
        for b in booklets:
            # TODO(report:004) verify Brickset instructions field name and URL pattern
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
