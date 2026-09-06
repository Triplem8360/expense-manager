from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from expense_api.models.expense import PaymentMethod


@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentMethodModel:
    id: int
    code: PaymentMethod
    display_name: str
    created_at: datetime
    updated_at: datetime
