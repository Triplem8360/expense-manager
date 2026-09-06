from __future__ import annotations

from typing import Annotated, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
    model_validator,
)

from expense_api.models import ExpenseSortField, PaymentMethod, SortDirection
from expense_api.schemas.category import CategoryName
from expense_api.schemas.expense import Currency, Merchant


class ExpenseListQuerySchema(BaseModel):
    """Validated filters, sorting, and pagination for the expense collection."""

    model_config = ConfigDict(extra="forbid")

    offset: Annotated[
        NonNegativeInt,
        Field(description="Number of matching expenses to skip"),
    ] = 0
    limit: Annotated[
        PositiveInt,
        Field(le=100, description="Maximum number of expenses to return"),
    ] = 20
    category: CategoryName | None = None
    currency: Currency | None = None
    payment_method: PaymentMethod | None = None
    merchant: Merchant | None = None
    spent_from: Annotated[
        AwareDatetime | None,
        Field(description="Inclusive lower bound for spent_at"),
    ] = None
    spent_to: Annotated[
        AwareDatetime | None,
        Field(description="Inclusive upper bound for spent_at"),
    ] = None
    sort_by: Annotated[
        ExpenseSortField,
        Field(description="Expense field used for sorting"),
    ] = "spent_at"
    sort_order: Annotated[
        SortDirection,
        Field(description="Ascending or descending sort direction"),
    ] = "desc"

    @model_validator(mode="after")
    def validate_spent_range(self) -> Self:
        if (
            self.spent_from is not None
            and self.spent_to is not None
            and self.spent_from > self.spent_to
        ):
            raise ValueError("spent_from must be earlier than or equal to spent_to")
        return self
