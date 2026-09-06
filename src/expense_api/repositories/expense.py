from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from expense_api.db.models import (
    CategoryRecord,
    ExpenseRecord,
    PaymentMethodRecord,
)
from expense_api.exceptions import ExpenseReferenceNotFoundError
from expense_api.models import (
    ExpenseModel,
    ExpenseSortField,
    PaymentMethod,
    SortDirection,
)

type ExpenseList = list[ExpenseModel]
type ExpensePageResult = tuple[ExpenseList, int]
type ExpenseDatabaseRow = tuple[ExpenseRecord, str, str]


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
    """Persist expenses through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ExpenseCreateData) -> ExpenseModel:
        category, payment_method = await self._resolve_references(
            category_name=data["category"],
            payment_method_code=data["payment_method"],
        )
        expense = ExpenseRecord(
            title=data["title"],
            description=data["description"],
            amount=data["amount"],
            currency=data["currency"],
            category_id=category.id,
            payment_method_id=payment_method.id,
            merchant=data["merchant"],
            spent_at=data["spent_at"],
            notes=data["notes"],
        )
        self._session.add(expense)
        await self._session.flush()
        await self._session.refresh(expense)

        result = self._to_domain_model(
            expense,
            category.name,
            payment_method.code,
        )
        await self._session.commit()
        return result

    async def list(self) -> list[ExpenseModel]:
        statement = self._expense_select().order_by(ExpenseRecord.id.asc())
        result = await self._session.execute(statement)
        return self._rows_to_domain_models(result.tuples().all())

    async def list_page(
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
        conditions: list[ColumnElement[bool]] = []
        if category is not None:
            conditions.append(func.lower(CategoryRecord.name) == category.casefold())
        if currency is not None:
            conditions.append(ExpenseRecord.currency == currency)
        if payment_method is not None:
            conditions.append(PaymentMethodRecord.code == payment_method.value)
        if merchant is not None:
            escaped_merchant = self._escape_like(merchant)
            conditions.append(
                ExpenseRecord.merchant.ilike(
                    f"%{escaped_merchant}%",
                    escape="\\",
                )
            )
        if spent_from is not None:
            conditions.append(ExpenseRecord.spent_at >= spent_from)
        if spent_to is not None:
            conditions.append(ExpenseRecord.spent_at <= spent_to)

        count_statement = (
            select(func.count(ExpenseRecord.id))
            .join(CategoryRecord, ExpenseRecord.category_id == CategoryRecord.id)
            .join(
                PaymentMethodRecord,
                ExpenseRecord.payment_method_id == PaymentMethodRecord.id,
            )
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement)

        sort_columns = {
            "spent_at": ExpenseRecord.spent_at,
            "created_at": ExpenseRecord.created_at,
            "updated_at": ExpenseRecord.updated_at,
            "amount": ExpenseRecord.amount,
            "title": func.lower(ExpenseRecord.title),
        }
        sort_column = sort_columns[sort_by]
        sort_expression = (
            sort_column.desc() if sort_order == "desc" else sort_column.asc()
        )
        statement = (
            self._expense_select()
            .where(*conditions)
            .order_by(sort_expression, ExpenseRecord.id.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        expenses = self._rows_to_domain_models(result.tuples().all())
        return expenses, total or 0

    async def get_by_id(self, expense_id: int) -> ExpenseModel | None:
        row = await self._get_database_row(expense_id)
        if row is None:
            return None
        return self._to_domain_model(*row)

    async def update(
        self,
        expense_id: int,
        changes: ExpenseUpdateData,
    ) -> ExpenseModel | None:
        row = await self._get_database_row(expense_id)
        if row is None:
            return None

        expense, category_name, payment_method_code = row
        if not changes:
            return self._to_domain_model(
                expense,
                category_name,
                payment_method_code,
            )

        if "category" in changes or "payment_method" in changes:
            category, payment_method = await self._resolve_references(
                category_name=changes.get("category", category_name),
                payment_method_code=changes.get(
                    "payment_method",
                    PaymentMethod(payment_method_code),
                ),
            )
            expense.category_id = category.id
            expense.payment_method_id = payment_method.id
            category_name = category.name
            payment_method_code = payment_method.code

        if "title" in changes:
            expense.title = changes["title"]
        if "description" in changes:
            expense.description = changes["description"]
        if "amount" in changes:
            expense.amount = changes["amount"]
        if "currency" in changes:
            expense.currency = changes["currency"]
        if "merchant" in changes:
            expense.merchant = changes["merchant"]
        if "spent_at" in changes:
            expense.spent_at = changes["spent_at"]
        if "notes" in changes:
            expense.notes = changes["notes"]

        expense.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(expense)

        result = self._to_domain_model(
            expense,
            category_name,
            payment_method_code,
        )
        await self._session.commit()
        return result

    async def delete(self, expense_id: int) -> bool:
        expense = await self._session.get(ExpenseRecord, expense_id)
        if expense is None:
            return False

        await self._session.delete(expense)
        await self._session.commit()
        return True

    async def _get_database_row(
        self,
        expense_id: int,
    ) -> ExpenseDatabaseRow | None:
        statement = self._expense_select().where(ExpenseRecord.id == expense_id)
        result = await self._session.execute(statement)
        return result.tuples().one_or_none()

    async def _resolve_references(
        self,
        *,
        category_name: str,
        payment_method_code: PaymentMethod,
    ) -> tuple[CategoryRecord, PaymentMethodRecord]:
        category = await self._session.scalar(
            select(CategoryRecord).where(CategoryRecord.name == category_name)
        )
        if category is None:
            raise ExpenseReferenceNotFoundError("category", category_name)

        payment_method = await self._session.scalar(
            select(PaymentMethodRecord).where(
                PaymentMethodRecord.code == payment_method_code.value
            )
        )
        if payment_method is None:
            raise ExpenseReferenceNotFoundError(
                "payment_method",
                payment_method_code.value,
            )
        return category, payment_method

    @staticmethod
    def _expense_select() -> Select[ExpenseDatabaseRow]:
        return (
            select(
                ExpenseRecord,
                CategoryRecord.name,
                PaymentMethodRecord.code,
            )
            .join(CategoryRecord, ExpenseRecord.category_id == CategoryRecord.id)
            .join(
                PaymentMethodRecord,
                ExpenseRecord.payment_method_id == PaymentMethodRecord.id,
            )
        )

    @staticmethod
    def _rows_to_domain_models(
        rows: Sequence[ExpenseDatabaseRow],
    ) -> ExpenseList:
        return [ExpenseRepository._to_domain_model(*row) for row in rows]

    @staticmethod
    def _to_domain_model(
        expense: ExpenseRecord,
        category_name: str,
        payment_method_code: str,
    ) -> ExpenseModel:
        return ExpenseModel(
            id=expense.id,
            title=expense.title,
            description=expense.description,
            amount=expense.amount,
            currency=expense.currency,
            category=category_name,
            payment_method=PaymentMethod(payment_method_code),
            merchant=expense.merchant,
            spent_at=expense.spent_at,
            notes=expense.notes,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
