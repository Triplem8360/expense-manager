from typing import Annotated

from pydantic import BaseModel, Field


class ErrorResponseSchema(BaseModel):
    """Structured error payload returned by application exception handlers."""

    status: Annotated[
        int,
        Field(ge=400, le=599, description="HTTP status code"),
    ]
    message: Annotated[
        str,
        Field(min_length=1, description="Human-readable error message"),
    ]
    details: Annotated[
        dict[str, str] | None,
        Field(description="Optional structured context about the error"),
    ] = None
