from expense_api.exceptions import PaymentMethodAlreadyExistsError
from expense_api.models import PaymentMethodModel
from expense_api.repositories import PaymentMethodRepository
from expense_api.schemas import PaymentMethodCreateSchema


class PaymentMethodService:
    """Apply payment-method management rules."""

    def __init__(self, repository: PaymentMethodRepository) -> None:
        self._repository = repository

    async def create_payment_method(
        self,
        data: PaymentMethodCreateSchema,
    ) -> PaymentMethodModel:
        if await self._repository.exists_with_code(data.code):
            raise PaymentMethodAlreadyExistsError(data.code.value)
        return await self._repository.create(
            code=data.code,
            display_name=data.display_name,
        )

    async def list_payment_methods(self) -> list[PaymentMethodModel]:
        return await self._repository.list()
