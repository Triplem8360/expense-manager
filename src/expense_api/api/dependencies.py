from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Header, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.api.cookies import validate_csrf_request
from expense_api.api.language import resolve_request_locale
from expense_api.core.config import Settings, get_settings
from expense_api.core.localization import (
    TranslationCatalog,
    Translator,
    get_translation_catalog,
)
from expense_api.db.session import get_session
from expense_api.exceptions import TokenValidationError
from expense_api.models import UserModel
from expense_api.repositories import (
    AuthRepository,
    CategoryRepository,
    ExpenseRepository,
    PaymentMethodRepository,
)
from expense_api.services import (
    AuthService,
    CategoryService,
    ExpenseService,
    PaymentMethodService,
)


def get_auth_repository(session: SessionDependency) -> AuthRepository:
    return AuthRepository(session)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    settings: SettingsDependency,
) -> AuthService:
    return AuthService(repository, settings)


def get_category_repository(session: SessionDependency) -> CategoryRepository:
    return CategoryRepository(session)


def get_category_service(
    repository: Annotated[CategoryRepository, Depends(get_category_repository)],
) -> CategoryService:
    return CategoryService(repository)


def get_expense_repository(
    session: SessionDependency,
) -> ExpenseRepository:
    return ExpenseRepository(session)


def get_expense_service(
    repository: Annotated[ExpenseRepository, Depends(get_expense_repository)],
) -> ExpenseService:
    return ExpenseService(repository)


def get_payment_method_repository(
    session: SessionDependency,
) -> PaymentMethodRepository:
    return PaymentMethodRepository(session)


def get_payment_method_service(
    repository: Annotated[
        PaymentMethodRepository,
        Depends(get_payment_method_repository),
    ],
) -> PaymentMethodService:
    return PaymentMethodService(repository)


def get_request_translator(
    catalog: Annotated[TranslationCatalog, Depends(get_translation_catalog)],
    language: Annotated[
        str | None,
        Query(
            alias="lang",
            min_length=2,
            max_length=35,
            pattern=r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$",
        ),
    ] = None,
    accept_language: Annotated[
        str | None,
        Header(alias="Accept-Language", max_length=512),
    ] = None,
) -> Translator:
    locale = resolve_request_locale(
        query_language=language,
        accept_language=accept_language,
        catalog=catalog,
    )
    return catalog.get_translator(locale)


def get_redis_client(request: Request) -> Redis:
    try:
        redis_client = request.app.state.redis_client
    except AttributeError as exc:
        raise RuntimeError(
            "Redis client is unavailable outside the application lifespan"
        ) from exc
    return cast(Redis, redis_client)


async def get_current_user(
    request: Request,
    service: AuthServiceDependency,
    settings: SettingsDependency,
) -> UserModel:
    access_token = request.cookies.get(settings.access_token_cookie_name)
    if access_token is None:
        raise TokenValidationError("access")

    user = await service.authenticate_access_token(access_token)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_csrf_request(request, settings)
    return user


SessionDependency = Annotated[AsyncSession, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
CategoryServiceDependency = Annotated[CategoryService, Depends(get_category_service)]
ExpenseServiceDependency = Annotated[ExpenseService, Depends(get_expense_service)]
PaymentMethodServiceDependency = Annotated[
    PaymentMethodService,
    Depends(get_payment_method_service),
]
CurrentUserDependency = Annotated[UserModel, Depends(get_current_user)]
TranslatorDependency = Annotated[Translator, Depends(get_request_translator)]
RedisClientDependency = Annotated[Redis, Depends(get_redis_client)]
