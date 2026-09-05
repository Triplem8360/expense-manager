from __future__ import annotations

from typing import cast

from expense_api.exceptions import ExpenseNotFoundError
from expense_api.models import ExpenseModel
from expense_api.repositories.expense import (
    ExpenseCreateData,
    ExpenseRepository,
    ExpenseUpdateData,
)
from expense_api.schemas import (
    ExpenseCreateSchema,
    ExpensePatchUpdateSchema,
    ExpensePutUpdateSchema,
)


class ExpenseService:
    """Coordinate expense application logic and persistence."""

    def __init__(self, repository: ExpenseRepository) -> None:
        self._repository = repository

    def create_expense(self, data: ExpenseCreateSchema) -> ExpenseModel:
        create_data: ExpenseCreateData = {
            "title": data.title,
            "description": data.description,
            "amount": data.amount,
            "currency": data.currency,
            "category": data.category,
            "payment_method": data.payment_method,
            "merchant": data.merchant,
            "spent_at": data.spent_at,
            "notes": data.notes,
        }
        return self._repository.create(create_data)

    def list_expenses(self) -> list[ExpenseModel]:
        return self._repository.list()

    def get_expense(self, expense_id: int) -> ExpenseModel:
        expense = self._repository.get_by_id(expense_id)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        return expense

    def replace_expense(
        self,
        expense_id: int,
        data: ExpensePutUpdateSchema,
    ) -> ExpenseModel:
        changes: ExpenseUpdateData = {
            "title": data.title,
            "description": data.description,
            "amount": data.amount,
            "currency": data.currency,
            "category": data.category,
            "payment_method": data.payment_method,
            "merchant": data.merchant,
            "spent_at": data.spent_at,
            "notes": data.notes,
        }
        return self._update_or_raise(expense_id, changes)

    def update_expense(
        self,
        expense_id: int,
        data: ExpensePatchUpdateSchema,
    ) -> ExpenseModel:
        changes = cast(
            ExpenseUpdateData,
            data.model_dump(exclude_unset=True),
        )
        return self._update_or_raise(expense_id, changes)

    def delete_expense(self, expense_id: int) -> None:
        if not self._repository.delete(expense_id):
            raise ExpenseNotFoundError(expense_id)

    def _update_or_raise(
        self,
        expense_id: int,
        changes: ExpenseUpdateData,
    ) -> ExpenseModel:
        expense = self._repository.update(expense_id, changes)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        return expense
