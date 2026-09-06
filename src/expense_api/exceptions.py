from typing import Literal

type ExpenseReferenceField = Literal["category", "payment_method"]


class CategoryAlreadyExistsError(Exception):
    """Raised when a category name is already registered."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Category already exists: {name}")


class ExpenseNotFoundError(Exception):
    """Raised when an expense cannot be found by its identifier."""

    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"Expense {expense_id} was not found")


class ExpenseReferenceNotFoundError(Exception):
    """Raised when an expense references unavailable lookup data."""

    def __init__(self, field: ExpenseReferenceField, value: str) -> None:
        self.field = field
        self.value = value
        super().__init__(f"Unknown {field}: {value}")


class PaymentMethodAlreadyExistsError(Exception):
    """Raised when a payment method code is already registered."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Payment method already exists: {code}")
