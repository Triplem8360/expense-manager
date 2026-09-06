from fastapi import APIRouter, Depends, status

from expense_api.api.dependencies import CategoryServiceDependency, get_current_user
from expense_api.models import CategoryModel
from expense_api.schemas import CategoryCreateSchema, CategoryReadSchema

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=CategoryReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: CategoryCreateSchema,
    service: CategoryServiceDependency,
) -> CategoryModel:
    return await service.create_category(data)


@router.get(
    "",
    response_model=list[CategoryReadSchema],
    status_code=status.HTTP_200_OK,
)
async def list_categories(
    service: CategoryServiceDependency,
) -> list[CategoryModel]:
    return await service.list_categories()
