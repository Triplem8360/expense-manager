from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class PaymentMethod(StrEnum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseModel:
    id: int
    title: str
    description: str
    amount: Decimal
    currency: str
    category: str
    payment_method: PaymentMethod
    merchant: str | None
    spent_at: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime
