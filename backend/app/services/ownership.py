from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from sqlalchemy.orm import Session

from app.models.owned import OwnedItem, OwnedStatus
from app.models.ownership import Ownership
from app.models.parts import SetPart


# DATA_MODEL.md: status -> default owned per manifest line
DEFAULT_OWNED_FRACTION = {
    OwnedStatus.complete: "full",       # default owned = quantity
    OwnedStatus.collecting: "zero",     # default owned = 0
    OwnedStatus.dismantled: "full",     # default owned = quantity (parts kept)
    OwnedStatus.wanted: "zero",         # n/a, wishlist
}


@dataclass
class OwnedMissing:
    owned: int
    missing: int


def default_owned(status: OwnedStatus, quantity: int) -> int:
    rule = DEFAULT_OWNED_FRACTION.get(status, "zero")
    return quantity if rule == "full" else 0


def overrides_for_owned_item(db: Session, owned_item_id: int, copy_index: int = 1) -> Dict[int, int]:
    rows = (
        db.query(Ownership)
        .filter(Ownership.owned_item_id == owned_item_id, Ownership.copy_index == copy_index)
        .all()
    )
    return {r.set_part_id: r.quantity_owned for r in rows}


def derive(owned_item: OwnedItem, set_parts: Iterable[SetPart], overrides: Dict[int, int]) -> Dict[int, OwnedMissing]:
    out: Dict[int, OwnedMissing] = {}
    for sp in set_parts:
        owned_default = default_owned(owned_item.status, sp.quantity)
        owned = overrides.get(sp.id, owned_default)
        owned = max(0, min(owned, sp.quantity))
        out[sp.id] = OwnedMissing(owned=owned, missing=max(0, sp.quantity - owned))
    return out


def rollup_totals(owned: Dict[int, OwnedMissing], parts: Iterable[SetPart]) -> Tuple[int, int]:
    total_owned = 0
    total_missing = 0
    for sp in parts:
        om = owned.get(sp.id)
        if om is None:
            continue
        total_owned += om.owned
        total_missing += om.missing
    return total_owned, total_missing


def upsert_override(
    db: Session,
    owned_item_id: int,
    set_part_id: int,
    quantity_owned: int,
    copy_index: int = 1,
) -> Ownership:
    row = (
        db.query(Ownership)
        .filter(
            Ownership.owned_item_id == owned_item_id,
            Ownership.copy_index == copy_index,
            Ownership.set_part_id == set_part_id,
        )
        .first()
    )
    if row is None:
        row = Ownership(
            owned_item_id=owned_item_id,
            copy_index=copy_index,
            set_part_id=set_part_id,
            quantity_owned=quantity_owned,
        )
        db.add(row)
    else:
        row.quantity_owned = quantity_owned
    return row


def resolve_set_part_id(db: Session, set_no: str, part_no: str, color_id: int) -> int | None:
    row = (
        db.query(SetPart)
        .filter(SetPart.set_no == set_no, SetPart.part_no == part_no, SetPart.color_id == color_id)
        .first()
    )
    return row.id if row else None
