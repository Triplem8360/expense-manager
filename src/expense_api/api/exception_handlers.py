from fastapi import Request, status
from fastapi.responses import JSONResponse

from expense_api.exceptions import (
    CategoryAlreadyExistsError,
    ExpenseNotFoundError,
    ExpenseReferenceNotFoundError,
    PaymentMethodAlreadyExistsError,
)


async def lookup_value_already_exists_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(
        exc,
        (CategoryAlreadyExistsError, PaymentMethodAlreadyExistsError),
    ):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


async def expense_not_found_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ExpenseNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def expense_reference_not_found_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ExpenseReferenceNotFoundError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": str(exc),
            "field": exc.field,
            "value": exc.value,
        },
    )
