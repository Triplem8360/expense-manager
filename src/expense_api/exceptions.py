from typing import Literal

type ExpenseReferenceField = Literal["category", "payment_method"]


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
