from fastapi import Request, status
from fastapi.responses import JSONResponse

from expense_api.api.cookies import clear_access_cookie, clear_auth_cookies
from expense_api.core.config import get_settings
from expense_api.exceptions import (
    AuthenticationError,
    CategoryAlreadyExistsError,
    CsrfValidationError,
    ExpenseNotFoundError,
    ExpenseReferenceNotFoundError,
    InactiveUserError,
    PaymentMethodAlreadyExistsError,
    TokenValidationError,
    UserAlreadyExistsError,
)


async def authentication_error_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, AuthenticationError):
        raise exc

    status_code = (
        status.HTTP_403_FORBIDDEN
        if isinstance(exc, (CsrfValidationError, InactiveUserError))
        else status.HTTP_401_UNAUTHORIZED
    )
    response = JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
        headers={"Cache-Control": "no-store"},
    )
    settings = get_settings()
    if isinstance(exc, InactiveUserError):
        clear_auth_cookies(response, settings)
    elif isinstance(exc, TokenValidationError):
        if exc.token_type == "refresh":
            clear_auth_cookies(response, settings)
        else:
            clear_access_cookie(response, settings)
    return response


async def user_already_exists_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, UserAlreadyExistsError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
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
