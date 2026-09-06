from __future__ import annotations

from decimal import Decimal
from typing import Annotated, ClassVar, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from expense_api.models import PaymentMethod

Title = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
        pattern=r"^[^\r\n\x00]+$",
    ),
    Field(
        description="Short expense title without line breaks",
        examples=["Team lunch"],
    ),
]
Description = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2_000,
        pattern=r"^[^\x00]+$",
    ),
    Field(
        description="Detailed explanation of the expense",
        examples=["Lunch during the FastAPI course"],
    ),
]
Amount = Annotated[
    Decimal,
    Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
        description="Positive monetary amount with at most two decimal places",
        examples=["24.50"],
    ),
]
Currency = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
    ),
    Field(
        description="Three-letter currency code",
        examples=["USD", "IRR"],
    ),
]
Category = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
    Field(description="Expense category", examples=["Food"]),
]
Merchant = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
        pattern=r"^[^\r\n\x00]+$",
    ),
    Field(description="Merchant or vendor name", examples=["Course Cafe"]),
]
Notes = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2_000,
        pattern=r"^[^\x00]+$",
    ),
    Field(description="Optional additional information about the expense"),
]


class _ExpenseRequiredFieldsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description
    amount: Amount
    currency: Currency
    category: Category
    payment_method: Annotated[
        PaymentMethod, 
        Field(description="How the expense was paid")
    ]
    spent_at: Annotated[
        AwareDatetime,
        Field(description="Timezone-aware date and time when the expense occurred"),
    ]


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
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

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

    id: PositiveInt
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

    @model_validator(mode="after")
    def validate_timestamp_order(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be later than or equal to created_at")
        return self


class ExpensePageSchema(BaseModel):
    items: Annotated[
        list[ExpenseReadSchema],
        Field(description="Expenses in the requested page"),
    ]
    total: Annotated[
        NonNegativeInt,
        Field(description="Total number of expenses matching the filters"),
    ]
    limit: Annotated[PositiveInt, Field(le=100)]
    offset: NonNegativeInt

    @model_validator(mode="after")
    def validate_page_metadata(self) -> Self:
        if len(self.items) > self.limit:
            raise ValueError("items cannot contain more entries than limit")
        if len(self.items) > self.total:
            raise ValueError("items cannot contain more entries than total")
        if self.items and self.offset + len(self.items) > self.total:
            raise ValueError("page range cannot exceed total")
        return self
