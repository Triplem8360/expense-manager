from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from expense_api.models import ExpenseModel, PaymentMethod


class ExpenseCreateData(TypedDict):
    title: str
    description: str
    amount: Decimal
    currency: str
    category: str
    payment_method: PaymentMethod
    merchant: str | None
    spent_at: datetime
    notes: str | None


class ExpenseUpdateData(TypedDict, total=False):
    title: str
    description: str
    amount: Decimal
    currency: str
    category: str
    payment_method: PaymentMethod
    merchant: str | None
    spent_at: datetime
    notes: str | None


class ExpenseRepository:
    """Store expenses in memory for the introductory API exercise."""

    def __init__(self, storage: dict[int, ExpenseModel] | None = None) -> None:
        self._expenses = storage if storage is not None else {}
        self._next_id = max(self._expenses, default=0) + 1

    def create(self, data: ExpenseCreateData) -> ExpenseModel:
        now = datetime.now(UTC)
        expense = ExpenseModel(
            id=self._next_id,
            created_at=now,
            updated_at=now,
            **data,
        )
        self._expenses[expense.id] = expense
        self._next_id += 1
        return expense

    def list(self) -> list[ExpenseModel]:
        return [self._expenses[expense_id] for expense_id in sorted(self._expenses)]

    def get_by_id(self, expense_id: int) -> ExpenseModel | None:
        return self._expenses.get(expense_id)

    def update(
        self,
        expense_id: int,
        changes: ExpenseUpdateData,
    ) -> ExpenseModel | None:
        expense = self.get_by_id(expense_id)
        if expense is None or not changes:
            return expense

        updated_expense = replace(
            expense,
            **changes,
            updated_at=datetime.now(UTC),
        )
        self._expenses[expense_id] = updated_expense
        return updated_expense

    def delete(self, expense_id: int) -> bool:
        return self._expenses.pop(expense_id, None) is not None
