from __future__ import annotations

from datetime import UTC, datetime
from hmac import compare_digest
from secrets import token_urlsafe

from fastapi import Request, Response

from expense_api.core.config import Settings
from expense_api.exceptions import CsrfValidationError
from expense_api.models import AuthSessionModel


def set_auth_cookies(
    response: Response,
    session: AuthSessionModel,
    settings: Settings,
) -> None:
    """Set authentication and double-submit CSRF cookies."""
    now = datetime.now(UTC)
    csrf_token = token_urlsafe(32)
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=session.access_token,
        max_age=max(0, int((session.access_token_expires_at - now).total_seconds())),
        expires=session.access_token_expires_at,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=session.refresh_token,
        max_age=max(0, int((session.refresh_token_expires_at - now).total_seconds())),
        expires=session.refresh_token_expires_at,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.set_cookie(
        key=settings.csrf_token_cookie_name,
        value=csrf_token,
        max_age=max(0, int((session.refresh_token_expires_at - now).total_seconds())),
        expires=session.refresh_token_expires_at,
        path="/",
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )
    response.headers["Cache-Control"] = "no-store"


def validate_csrf_request(request: Request, settings: Settings) -> None:
    cookie_token = request.cookies.get(settings.csrf_token_cookie_name)
    header_token = request.headers.get(settings.csrf_token_header_name)
    if (
        cookie_token is None
        or header_token is None
        or not compare_digest(cookie_token, header_token)
    ):
        raise CsrfValidationError


def clear_access_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.access_token_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    clear_access_cookie(response, settings)
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        key=settings.csrf_token_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )
