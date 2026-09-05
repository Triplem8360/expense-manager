from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from expense_api.models import (
    ExpenseModel,
    ExpenseSortField,
    PaymentMethod,
    SortDirection,
)

type ExpensePageResult = tuple[list[ExpenseModel], int]


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

    def list_page(
        self,
        *,
        offset: int,
        limit: int,
        category: str | None = None,
        currency: str | None = None,
        payment_method: PaymentMethod | None = None,
        merchant: str | None = None,
        spent_from: datetime | None = None,
        spent_to: datetime | None = None,
        sort_by: ExpenseSortField = "spent_at",
        sort_order: SortDirection = "desc",
    ) -> ExpensePageResult:
        expenses = self.list()

        if category is not None:
            category_filter = category.casefold()
            expenses = [
                expense
                for expense in expenses
                if expense.category.casefold() == category_filter
            ]
        if currency is not None:
            expenses = [expense for expense in expenses if expense.currency == currency]
        if payment_method is not None:
            expenses = [
                expense
                for expense in expenses
                if expense.payment_method is payment_method
            ]
        if merchant is not None:
            merchant_filter = merchant.casefold()
            expenses = [
                expense
                for expense in expenses
                if expense.merchant is not None
                and merchant_filter in expense.merchant.casefold()
            ]
        if spent_from is not None:
            expenses = [
                expense for expense in expenses if expense.spent_at >= spent_from
            ]
        if spent_to is not None:
            expenses = [expense for expense in expenses if expense.spent_at <= spent_to]

        reverse = sort_order == "desc"
        if sort_by == "title":
            expenses.sort(key=lambda expense: expense.title.casefold(), reverse=reverse)
        elif sort_by == "amount":
            expenses.sort(key=lambda expense: expense.amount, reverse=reverse)
        elif sort_by == "created_at":
            expenses.sort(key=lambda expense: expense.created_at, reverse=reverse)
        elif sort_by == "updated_at":
            expenses.sort(key=lambda expense: expense.updated_at, reverse=reverse)
        else:
            expenses.sort(key=lambda expense: expense.spent_at, reverse=reverse)

        total = len(expenses)
        return expenses[offset : offset + limit], total

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
