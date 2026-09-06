from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class CategoryModel:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
