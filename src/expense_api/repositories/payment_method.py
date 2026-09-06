from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.db.models import PaymentMethodRecord
from expense_api.models import PaymentMethod, PaymentMethodModel


class PaymentMethodRepository:
    """Persist and retrieve supported payment methods."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        code: PaymentMethod,
        display_name: str,
    ) -> PaymentMethodModel:
        payment_method = PaymentMethodRecord(
            code=code.value,
            display_name=display_name,
        )
        self._session.add(payment_method)
        await self._session.flush()
        await self._session.refresh(payment_method)

        result = self._to_domain_model(payment_method)
        await self._session.commit()
        return result

    async def list(self) -> list[PaymentMethodModel]:
        statement = select(PaymentMethodRecord).order_by(
            func.lower(PaymentMethodRecord.display_name).asc(),
            PaymentMethodRecord.id.asc(),
        )
        payment_methods = await self._session.scalars(statement)
        return [
            self._to_domain_model(payment_method) for payment_method in payment_methods
        ]

    async def exists_with_code(self, code: PaymentMethod) -> bool:
        statement = select(PaymentMethodRecord.id).where(
            PaymentMethodRecord.code == code.value
        )
        return await self._session.scalar(statement) is not None

    @staticmethod
    def _to_domain_model(
        payment_method: PaymentMethodRecord,
    ) -> PaymentMethodModel:
        return PaymentMethodModel(
            id=payment_method.id,
            code=PaymentMethod(payment_method.code),
            display_name=payment_method.display_name,
            created_at=payment_method.created_at,
            updated_at=payment_method.updated_at,
        )
