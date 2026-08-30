class ExpenseNotFoundError(Exception):
    """Raised when an expense cannot be found by its identifier."""

    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"Expense {expense_id} was not found")
