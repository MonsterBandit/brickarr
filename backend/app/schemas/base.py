from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PagedEnvelope(CamelModel, Generic[T]):
    page: int = 1
    page_size: int = 50
    sort_key: str | None = None
    sort_direction: str | None = None
    total_records: int = 0
    records: List[T] = []
