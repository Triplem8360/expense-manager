from __future__ import annotations

from decimal import Decimal
from typing import Annotated, ClassVar, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from expense_api.models import PaymentMethod

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2_000),
]
Amount = Annotated[
    Decimal,
    Field(gt=0, max_digits=14, decimal_places=2),
]
Currency = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=3,
        max_length=3,
    ),
]
Category = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
Merchant = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
Notes = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2_000),
]


class _ExpenseRequiredFieldsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description
    amount: Amount
    currency: Currency
    category: Category
    payment_method: PaymentMethod
    spent_at: AwareDatetime


class ExpenseCreateSchema(_ExpenseRequiredFieldsSchema):
    merchant: Merchant | None = None
    notes: Notes | None = None


class ExpensePutUpdateSchema(_ExpenseRequiredFieldsSchema):
    """A complete replacement of all client-editable expense fields."""

    merchant: Merchant | None
    notes: Notes | None


class ExpensePatchUpdateSchema(BaseModel):
    """A partial update containing only client-provided fields."""

    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: Description | None = None
    amount: Amount | None = None
    currency: Currency | None = None
    category: Category | None = None
    payment_method: PaymentMethod | None = None
    merchant: Merchant | None = None
    spent_at: AwareDatetime | None = None
    notes: Notes | None = None

    _NON_NULLABLE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "title",
            "description",
            "amount",
            "currency",
            "category",
            "payment_method",
            "spent_at",
        }
    )

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> Self:
        null_fields = sorted(
            field_name
            for field_name in self._NON_NULLABLE_FIELDS
            if field_name in self.model_fields_set and getattr(self, field_name) is None
        )
        if null_fields:
            fields = ", ".join(null_fields)
            raise ValueError(f"These fields cannot be null: {fields}")
        return self


class ExpenseReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(gt=0)]
    title: Title
    description: Description
    amount: Amount
    currency: Currency
    category: Category
    payment_method: PaymentMethod
    merchant: Merchant | None
    spent_at: AwareDatetime
    notes: Notes | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
