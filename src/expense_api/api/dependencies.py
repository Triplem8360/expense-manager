from typing import Annotated, cast

from fastapi import Depends, Request

from expense_api.repositories import ExpenseRepository
from expense_api.services import ExpenseService


def get_expense_repository(request: Request) -> ExpenseRepository:
    return cast(ExpenseRepository, request.app.state.expense_repository)


def get_expense_service(
    repository: Annotated[ExpenseRepository, Depends(get_expense_repository)],
) -> ExpenseService:
    return ExpenseService(repository)


ExpenseServiceDependency = Annotated[ExpenseService, Depends(get_expense_service)]
