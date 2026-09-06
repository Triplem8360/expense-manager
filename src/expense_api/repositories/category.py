from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.db.models import CategoryRecord
from expense_api.models import CategoryModel


class CategoryRepository:
    """Persist and retrieve expense categories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        description: str | None,
    ) -> CategoryModel:
        category = CategoryRecord(name=name, description=description)
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)

        result = self._to_domain_model(category)
        await self._session.commit()
        return result

    async def list(self) -> list[CategoryModel]:
        statement = select(CategoryRecord).order_by(
            func.lower(CategoryRecord.name).asc(),
            CategoryRecord.id.asc(),
        )
        categories = await self._session.scalars(statement)
        return [self._to_domain_model(category) for category in categories]

    async def exists_with_name(self, name: str) -> bool:
        statement = select(CategoryRecord.id).where(CategoryRecord.name == name)
        return await self._session.scalar(statement) is not None

    @staticmethod
    def _to_domain_model(category: CategoryRecord) -> CategoryModel:
        return CategoryModel(
            id=category.id,
            name=category.name,
            description=category.description,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
