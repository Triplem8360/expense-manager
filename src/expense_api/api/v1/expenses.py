from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from expense_api.api.dependencies import ExpenseServiceDependency, get_current_user
from expense_api.models import ExpenseModel
from expense_api.schemas import (
    ErrorResponseSchema,
    ExpenseCreateSchema,
    ExpenseListQuerySchema,
    ExpensePageSchema,
    ExpensePatchUpdateSchema,
    ExpensePutUpdateSchema,
    ExpenseReadSchema,
)

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(get_current_user)],
)
ExpenseId = Annotated[int, Path(gt=0, description="Expense identifier")]
EXPENSE_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponseSchema,
        "description": (
            "Returned when no expense exists for the requested `expense_id`. "
            "The message is translated according to the resolved request language."
        ),
        "headers": {
            "Content-Language": {
                "description": "Language used for the error message",
                "schema": {
                    "type": "string",
                    "example": "en",
                },
            }
        },
        "content": {
            "application/json": {
                "examples": {
                    "english": {
                        "summary": "Expense not found in English",
                        "value": {
                            "status": status.HTTP_404_NOT_FOUND,
                            "message": "Expense 123 was not found",
                        },
                    },
                    "persian": {
                        "summary": "Expense not found in Persian",
                        "value": {
                            "status": status.HTTP_404_NOT_FOUND,
                            "message": "هزینه با شناسه 123 پیدا نشد.",
                        },
                    },
                }
            }
        },
    }
}


@router.post(
    "",
    response_model=ExpenseReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    data: ExpenseCreateSchema,
    service: ExpenseServiceDependency,
) -> ExpenseModel:
    return await service.create_expense(data)


@router.get(
    "",
    response_model=ExpensePageSchema,
    status_code=status.HTTP_200_OK,
)
async def list_expenses(
    service: ExpenseServiceDependency,
    query: Annotated[ExpenseListQuerySchema, Query()],
) -> ExpensePageSchema:
    expenses, total = await service.list_expenses(query)
    return ExpensePageSchema(
        items=[ExpenseReadSchema.model_validate(expense) for expense in expenses],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/{expense_id}",
    response_model=ExpenseReadSchema,
    status_code=status.HTTP_200_OK,
    responses=EXPENSE_NOT_FOUND_RESPONSE,
)
async def get_expense(
    expense_id: ExpenseId,
    service: ExpenseServiceDependency,
) -> ExpenseModel:
    return await service.get_expense(expense_id)


@router.put(
    "/{expense_id}",
    response_model=ExpenseReadSchema,
    status_code=status.HTTP_200_OK,
    responses=EXPENSE_NOT_FOUND_RESPONSE,
)
async def replace_expense(
    expense_id: ExpenseId,
    data: ExpensePutUpdateSchema,
    service: ExpenseServiceDependency,
) -> ExpenseModel:
    return await service.replace_expense(expense_id, data)


@router.patch(
    "/{expense_id}",
    response_model=ExpenseReadSchema,
    status_code=status.HTTP_200_OK,
    responses=EXPENSE_NOT_FOUND_RESPONSE,
)
async def update_expense(
    expense_id: ExpenseId,
    data: ExpensePatchUpdateSchema,
    service: ExpenseServiceDependency,
) -> ExpenseModel:
    return await service.update_expense(expense_id, data)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=EXPENSE_NOT_FOUND_RESPONSE,
)
async def delete_expense(
    expense_id: ExpenseId,
    service: ExpenseServiceDependency,
) -> Response:
    await service.delete_expense(expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
