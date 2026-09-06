from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.api.cookies import validate_csrf_request
from expense_api.core.config import Settings, get_settings
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
