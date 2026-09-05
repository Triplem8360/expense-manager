from __future__ import annotations

from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from expense_api.models import ExpenseSortField, PaymentMethod, SortDirection
from expense_api.schemas.expense import Category, Currency, Merchant


class ExpenseListQuerySchema(BaseModel):
    """Validated filters, sorting, and pagination for the expense collection."""

    model_config = ConfigDict(extra="forbid")

    offset: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=100)] = 20
    category: Category | None = None
    currency: Currency | None = None
    payment_method: PaymentMethod | None = None
    merchant: Merchant | None = None
    spent_from: AwareDatetime | None = None
    spent_to: AwareDatetime | None = None
    sort_by: ExpenseSortField = "spent_at"
    sort_order: SortDirection = "desc"

    @model_validator(mode="after")
    def validate_spent_range(self) -> Self:
        if (
            self.spent_from is not None
            and self.spent_to is not None
            and self.spent_from > self.spent_to
        ):
            raise ValueError("spent_from must be earlier than or equal to spent_to")
        return self
