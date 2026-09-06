from fastapi import APIRouter, Depends, status

from expense_api.api.dependencies import (
    PaymentMethodServiceDependency,
    get_current_user,
)
from expense_api.models import PaymentMethodModel
from expense_api.schemas import PaymentMethodCreateSchema, PaymentMethodReadSchema

router = APIRouter(
    prefix="/payment-methods",
    tags=["payment-methods"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=PaymentMethodReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_method(
    data: PaymentMethodCreateSchema,
    service: PaymentMethodServiceDependency,
) -> PaymentMethodModel:
    return await service.create_payment_method(data)


@router.get(
    "",
    response_model=list[PaymentMethodReadSchema],
    status_code=status.HTTP_200_OK,
)
async def list_payment_methods(
    service: PaymentMethodServiceDependency,
) -> list[PaymentMethodModel]:
    return await service.list_payment_methods()
