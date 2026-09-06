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

CategoryName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
        pattern=r"^[^\r\n\x00]+$",
    ),
]
CategoryDescription = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2_000,
        pattern=r"^[^\x00]+$",
    ),
]


class CategoryCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        CategoryName,
        Field(description="Unique category name", examples=["Food"]),
    ]
    description: Annotated[
        CategoryDescription | None,
        Field(description="Optional category description"),
    ] = None


class CategoryReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt
    name: CategoryName
    description: CategoryDescription | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
