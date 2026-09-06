from __future__ import annotations

from typing import Annotated

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    StringConstraints,
)

from expense_api.models import PaymentMethod

PaymentMethodDisplayName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[^\r\n\x00]+$",
    ),
]


class PaymentMethodCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Annotated[
        PaymentMethod,
        Field(description="Payment method code used by expense requests"),
    ]
    display_name: Annotated[
        PaymentMethodDisplayName,
        Field(description="Human-readable payment method name", examples=["Cash"]),
    ]


class PaymentMethodReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt
    code: PaymentMethod
    display_name: PaymentMethodDisplayName
    created_at: AwareDatetime
    updated_at: AwareDatetime
