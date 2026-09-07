from fastapi import Request, status
from fastapi.responses import JSONResponse

from expense_api.api.cookies import clear_access_cookie, clear_auth_cookies
from expense_api.api.language import get_translator_for_request, set_content_language
from expense_api.core.config import get_settings
from expense_api.core.localization import Translator, get_translation_catalog
from expense_api.exceptions import (
    AuthenticationError,
    CategoryAlreadyExistsError,
    CsrfValidationError,
    ExpenseNotFoundError,
    ExpenseReferenceNotFoundError,
    InactiveUserError,
    InvalidCredentialsError,
    PaymentMethodAlreadyExistsError,
    RefreshTokenReuseError,
    TokenExpiredError,
    TokenValidationError,
    UserAlreadyExistsError,
)


async def authentication_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, AuthenticationError):
        raise exc

    translator = _translator_for_request(request)
    status_code = (
        status.HTTP_403_FORBIDDEN
        if isinstance(exc, (CsrfValidationError, InactiveUserError))
        else status.HTTP_401_UNAUTHORIZED
    )
    response = _localized_json_response(
        translator=translator,
        status_code=status_code,
        content={"detail": _authentication_error_detail(exc, translator)},
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
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, UserAlreadyExistsError):
        raise exc
    translator = _translator_for_request(request)
    return _localized_json_response(
        translator=translator,
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": translator.gettext("A user with this email already exists"),
        },
    )


async def lookup_value_already_exists_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(
        exc,
        (CategoryAlreadyExistsError, PaymentMethodAlreadyExistsError),
    ):
        raise exc
    translator = _translator_for_request(request)
    if isinstance(exc, CategoryAlreadyExistsError):
        detail = translator.gettext("Category already exists: %(name)s") % {
            "name": exc.name,
        }
    else:
        detail = translator.gettext(
            "Payment method already exists: %(code)s"
        ) % {"code": exc.code}

    return _localized_json_response(
        translator=translator,
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail},
    )


async def expense_not_found_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ExpenseNotFoundError):
        raise exc
    translator = _translator_for_request(request)
    detail = translator.gettext("Expense %(expense_id)s was not found") % {
        "expense_id": exc.expense_id,
    }
    return _localized_json_response(
        translator=translator,
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": detail},
    )


async def expense_reference_not_found_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, ExpenseReferenceNotFoundError):
        raise exc
    translator = _translator_for_request(request)
    if exc.field == "category":
        detail = translator.gettext("Unknown category: %(value)s") % {
            "value": exc.value,
        }
    else:
        detail = translator.gettext("Unknown payment method: %(value)s") % {
            "value": exc.value,
        }

    return _localized_json_response(
        translator=translator,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": detail,
            "field": exc.field,
            "value": exc.value,
        },
    )


def _translator_for_request(request: Request) -> Translator:
    return get_translator_for_request(request, get_translation_catalog())


def _localized_json_response(
    *,
    translator: Translator,
    status_code: int,
    content: dict[str, object],
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )
    set_content_language(response, translator.locale)
    return response


def _authentication_error_detail(
    exc: AuthenticationError,
    translator: Translator,
) -> str:
    _ = translator.gettext
    if isinstance(exc, CsrfValidationError):
        return _("CSRF token is missing or invalid")
    if isinstance(exc, InactiveUserError):
        return _("User account is inactive")
    if isinstance(exc, InvalidCredentialsError):
        return _("Invalid email or password")
    if isinstance(exc, RefreshTokenReuseError):
        return _("Refresh token reuse detected")
    if isinstance(exc, TokenExpiredError):
        if exc.token_type == "refresh":
            return _("Refresh token has expired")
        return _("Access token has expired")
    if isinstance(exc, TokenValidationError):
        if exc.token_type == "refresh":
            return _("Refresh token is invalid")
        return _("Access token is invalid")
    return _("Authentication failed")
