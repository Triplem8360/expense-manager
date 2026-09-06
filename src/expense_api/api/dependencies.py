from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.db.session import get_session
from expense_api.repositories import (
    CategoryRepository,
    ExpenseRepository,
    PaymentMethodRepository,
)
from expense_api.services import (
    CategoryService,
    ExpenseService,
    PaymentMethodService,
)

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


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


CategoryServiceDependency = Annotated[CategoryService, Depends(get_category_service)]
ExpenseServiceDependency = Annotated[ExpenseService, Depends(get_expense_service)]
PaymentMethodServiceDependency = Annotated[
    PaymentMethodService,
    Depends(get_payment_method_service),
]
