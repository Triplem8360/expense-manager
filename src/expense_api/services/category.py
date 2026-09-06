from expense_api.exceptions import CategoryAlreadyExistsError
from expense_api.models import CategoryModel
from expense_api.repositories import CategoryRepository
from expense_api.schemas import CategoryCreateSchema


class CategoryService:
    """Apply category management rules."""

    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def create_category(self, data: CategoryCreateSchema) -> CategoryModel:
        if await self._repository.exists_with_name(data.name):
            raise CategoryAlreadyExistsError(data.name)
        return await self._repository.create(
            name=data.name,
            description=data.description,
        )

    async def list_categories(self) -> list[CategoryModel]:
        return await self._repository.list()
