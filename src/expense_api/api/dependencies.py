from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.db.session import get_session
from expense_api.repositories import ExpenseRepository
from expense_api.services import ExpenseService


def get_expense_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExpenseRepository:
    return ExpenseRepository(session)


def get_expense_service(
    repository: Annotated[ExpenseRepository, Depends(get_expense_repository)],
) -> ExpenseService:
    return ExpenseService(repository)


ExpenseServiceDependency = Annotated[ExpenseService, Depends(get_expense_service)]
