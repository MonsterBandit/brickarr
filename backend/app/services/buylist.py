from __future__ import annotations

import csv
import io
from typing import Iterable, List, Tuple

from sqlalchemy.orm import Session

from app.models.owned import OwnedItem
from app.models.parts import PartItemType, SetPart
from app.services.ownership import derive, overrides_for_owned_item


def _missing_lines(db: Session, owned_item: OwnedItem) -> List[Tuple[SetPart, int]]:
    parts = db.query(SetPart).filter(SetPart.set_no == owned_item.item_no).all()
    overrides = overrides_for_owned_item(db, owned_item.id)
    om = derive(owned_item, parts, overrides)
    out: List[Tuple[SetPart, int]] = []
    for sp in parts:
        miss = om[sp.id].missing
        if miss > 0:
            out.append((sp, miss))
    return out


def _xml_type(part_item_type: PartItemType) -> str:
    return "M" if part_item_type == PartItemType.MINIFIG else "P"


def render_xml(lines: Iterable[Tuple[SetPart, int]]) -> str:
    buf = io.StringIO()
    buf.write("<INVENTORY>\n")
    for sp, qty in lines:
        buf.write(
            f"  <ITEM><ITEMTYPE>{_xml_type(sp.part_item_type)}</ITEMTYPE>"
            f"<ITEMID>{sp.part_no}</ITEMID>"
            f"<COLOR>{sp.color_id}</COLOR>"
            f"<MINQTY>{qty}</MINQTY></ITEM>\n"
        )
    buf.write("</INVENTORY>\n")
    return buf.getvalue()


def render_csv(lines: Iterable[Tuple[SetPart, int]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["itemType", "itemNo", "colorId", "minQty"])
    for sp, qty in lines:
        w.writerow([_xml_type(sp.part_item_type), sp.part_no, sp.color_id, qty])
    return buf.getvalue()


def render_json(lines: Iterable[Tuple[SetPart, int]]) -> dict:
    return {
        "records": [
            {
                "itemType": _xml_type(sp.part_item_type),
                "itemNo": sp.part_no,
                "colorId": sp.color_id,
                "minQty": qty,
            }
            for sp, qty in lines
        ]
    }


def buylist_for_set(db: Session, owned_item: OwnedItem, fmt: str) -> tuple[str, str]:
    lines = _missing_lines(db, owned_item)
    f = (fmt or "xml").lower()
    if f == "csv":
        return render_csv(lines), "text/csv"
    if f == "json":
        import json
        return json.dumps(render_json(lines)), "application/json"
    return render_xml(lines), "application/xml"


def buylist_for_collection(db: Session, owned_items: Iterable[OwnedItem], fmt: str) -> tuple[str, str]:
    consolidated: dict[tuple[str, str, int], int] = {}
    for oi in owned_items:
        for sp, qty in _missing_lines(db, oi):
            key = (_xml_type(sp.part_item_type), sp.part_no, sp.color_id)
            consolidated[key] = consolidated.get(key, 0) + qty
    rows: List[tuple] = list(consolidated.items())
    f = (fmt or "xml").lower()
    if f == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["itemType", "itemNo", "colorId", "minQty"])
        for (itype, ino, cid), qty in rows:
            w.writerow([itype, ino, cid, qty])
        return buf.getvalue(), "text/csv"
    if f == "json":
        import json
        return json.dumps({
            "records": [
                {"itemType": k[0], "itemNo": k[1], "colorId": k[2], "minQty": v}
                for k, v in rows
            ]
        }), "application/json"
    buf = io.StringIO()
    buf.write("<INVENTORY>\n")
    for (itype, ino, cid), qty in rows:
        buf.write(
            f"  <ITEM><ITEMTYPE>{itype}</ITEMTYPE><ITEMID>{ino}</ITEMID>"
            f"<COLOR>{cid}</COLOR><MINQTY>{qty}</MINQTY></ITEM>\n"
        )
    buf.write("</INVENTORY>\n")
    return buf.getvalue(), "application/xml"
