from __future__ import annotations

from typing import cast

from expense_api.cache import ExpenseCache
from expense_api.exceptions import ExpenseNotFoundError
from expense_api.models import ExpenseModel
from expense_api.repositories.expense import (
    ExpenseCreateData,
    ExpensePageResult,
    ExpenseRepository,
    ExpenseUpdateData,
)
from expense_api.schemas import (
    ExpenseCreateSchema,
    ExpenseListQuerySchema,
    ExpensePatchUpdateSchema,
    ExpensePutUpdateSchema,
)


class ExpenseService:
    """Coordinate expense application logic and persistence."""

    def __init__(self, repository: ExpenseRepository, cache: ExpenseCache) -> None:
        self._repository = repository
        self._cache = cache

    async def create_expense(self, data: ExpenseCreateSchema) -> ExpenseModel:
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
        expense = await self._repository.create(create_data)
        await self._cache.sync_after_write(expense)
        return expense

    async def list_expenses(self, query: ExpenseListQuerySchema) -> ExpensePageResult:
        cache_key, cached_page = await self._cache.get_page(query.model_dump_json())
        if cached_page is not None:
            return cached_page

        expenses, total = await self._repository.list_page(
            offset=query.offset,
            limit=query.limit,
            category=query.category,
            currency=query.currency,
            payment_method=query.payment_method,
            merchant=query.merchant,
            spent_from=query.spent_from,
            spent_to=query.spent_to,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        await self._cache.set_page(cache_key, expenses, total)
        return expenses, total

    async def get_expense(self, expense_id: int) -> ExpenseModel:
        cached_expense = await self._cache.get_expense(expense_id)
        if cached_expense is not None:
            return cached_expense

        expense = await self._repository.get_by_id(expense_id)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        await self._cache.set_expense(expense)
        return expense

    async def replace_expense(
        self, expense_id: int, data: ExpensePutUpdateSchema
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
        return await self._update_or_raise(expense_id, changes)

    async def update_expense(
        self,
        expense_id: int,
        data: ExpensePatchUpdateSchema,
    ) -> ExpenseModel:
        changes = cast(
            ExpenseUpdateData,
            data.model_dump(exclude_unset=True),
        )
        return await self._update_or_raise(expense_id, changes)

    async def delete_expense(self, expense_id: int) -> None:
        if not await self._repository.delete(expense_id):
            raise ExpenseNotFoundError(expense_id)
        await self._cache.sync_after_delete(expense_id)

    async def _update_or_raise(
        self,
        expense_id: int,
        changes: ExpenseUpdateData,
    ) -> ExpenseModel:
        expense = await self._repository.update(expense_id, changes)
        if expense is None:
            raise ExpenseNotFoundError(expense_id)
        await self._cache.sync_after_write(expense)
        return expense
