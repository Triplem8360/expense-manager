from __future__ import annotations

import hashlib
import logging
from decimal import Decimal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    ValidationError,
)
from redis.asyncio import Redis
from redis.exceptions import RedisError

from expense_api.models import ExpenseModel, PaymentMethod

logger = logging.getLogger(__name__)

type ExpensePage = tuple[list[ExpenseModel], int]
type ExpensePageCacheLookup = tuple[str | None, ExpensePage | None]


class _CachedExpenseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: PositiveInt
    title: str
    description: str
    amount: Decimal
    currency: str
    category: str
    payment_method: PaymentMethod
    merchant: str | None
    spent_at: AwareDatetime
    notes: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @classmethod
    def from_domain_model(cls, expense: ExpenseModel) -> _CachedExpenseSchema:
        return cls(
            id=expense.id,
            title=expense.title,
            description=expense.description,
            amount=expense.amount,
            currency=expense.currency,
            category=expense.category,
            payment_method=expense.payment_method,
            merchant=expense.merchant,
            spent_at=expense.spent_at,
            notes=expense.notes,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )

    def to_domain_model(self) -> ExpenseModel:
        return ExpenseModel(
            id=self.id,
            title=self.title,
            description=self.description,
            amount=self.amount,
            currency=self.currency,
            category=self.category,
            payment_method=self.payment_method,
            merchant=self.merchant,
            spent_at=self.spent_at,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class _CachedExpensePageSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[_CachedExpenseSchema]
    total: NonNegativeInt


class ExpenseCache:
    """Cache expense reads and invalidate them after successful mutations."""

    def __init__(
        self,
        client: Redis,
        *,
        key_prefix: str,
        ttl_seconds: int,
    ) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._namespace = f"{key_prefix}:v1:expenses"
        self._page_generation_key = f"{self._namespace}:pages:generation"

    async def get_expense(self, expense_id: int) -> ExpenseModel | None:
        key = self._expense_key(expense_id)
        try:
            cached = await self._client.get(key)
        except RedisError:
            self._log_redis_failure("read", key)
            return None

        if cached is None:
            return None

        try:
            return _CachedExpenseSchema.model_validate_json(cached).to_domain_model()
        except ValidationError:
            await self._discard_invalid_entry(key)
            return None

    async def set_expense(self, expense: ExpenseModel) -> None:
        key = self._expense_key(expense.id)
        payload = _CachedExpenseSchema.from_domain_model(expense).model_dump_json()
        try:
            await self._client.set(key, payload, ex=self._ttl_seconds)
        except RedisError:
            self._log_redis_failure("write", key)

    async def get_page(self, query_key: str) -> ExpensePageCacheLookup:
        try:
            generation = await self._client.get(self._page_generation_key)
            key = self._page_key(str(generation or "0"), query_key)
            cached = await self._client.get(key)
        except RedisError:
            self._log_redis_failure("read", self._page_generation_key)
            return None, None

        if cached is None:
            return key, None

        try:
            page = _CachedExpensePageSchema.model_validate_json(cached)
        except ValidationError:
            await self._discard_invalid_entry(key)
            return key, None

        return key, ([item.to_domain_model() for item in page.items], page.total)

    async def set_page(
        self,
        key: str | None,
        expenses: list[ExpenseModel],
        total: int,
    ) -> None:
        if key is None:
            return

        payload = _CachedExpensePageSchema(
            items=[
                _CachedExpenseSchema.from_domain_model(expense) for expense in expenses
            ],
            total=total,
        ).model_dump_json()
        try:
            await self._client.set(key, payload, ex=self._ttl_seconds)
        except RedisError:
            self._log_redis_failure("write", key)

    async def sync_after_write(self, expense: ExpenseModel) -> None:
        key = self._expense_key(expense.id)
        payload = _CachedExpenseSchema.from_domain_model(expense).model_dump_json()
        try:
            async with self._client.pipeline(transaction=True) as pipeline:
                pipeline.set(key, payload, ex=self._ttl_seconds)
                pipeline.incr(self._page_generation_key)
                await pipeline.execute()
        except RedisError:
            self._log_redis_failure("refresh", key)

    async def sync_after_delete(self, expense_id: int) -> None:
        key = self._expense_key(expense_id)
        try:
            async with self._client.pipeline(transaction=True) as pipeline:
                pipeline.delete(key)
                pipeline.incr(self._page_generation_key)
                await pipeline.execute()
        except RedisError:
            self._log_redis_failure("invalidate", key)

    def _expense_key(self, expense_id: int) -> str:
        return f"{self._namespace}:item:{expense_id}"

    def _page_key(self, generation: str, query_key: str) -> str:
        query_digest = hashlib.sha256(query_key.encode()).hexdigest()
        return f"{self._namespace}:pages:{generation}:{query_digest}"

    async def _discard_invalid_entry(self, key: str) -> None:
        logger.warning("Discarding invalid Redis cache entry for key %s", key)
        try:
            await self._client.delete(key)
        except RedisError:
            self._log_redis_failure("delete invalid", key)

    @staticmethod
    def _log_redis_failure(operation: str, key: str) -> None:
        logger.warning(
            "Unable to %s Redis cache key %s; using PostgreSQL fallback",
            operation,
            key,
            exc_info=True,
        )
