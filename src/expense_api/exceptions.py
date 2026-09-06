from typing import Literal

type ExpenseReferenceField = Literal["category", "payment_method"]
type AuthenticationTokenType = Literal["access", "refresh"]


class AuthenticationError(Exception):
    """Base exception for failed authentication."""


class CsrfValidationError(AuthenticationError):
    """Raised when cookie authentication lacks a valid CSRF token."""

    def __init__(self) -> None:
        super().__init__("CSRF token is missing or invalid")


class InactiveUserError(AuthenticationError):
    """Raised when an inactive user attempts to authenticate."""

    def __init__(self) -> None:
        super().__init__("User account is inactive")


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials cannot be verified."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class TokenValidationError(AuthenticationError):
    """Raised when an authentication token is invalid."""

    def __init__(self, token_type: AuthenticationTokenType) -> None:
        self.token_type = token_type
        super().__init__(f"Invalid {token_type} token")


class TokenExpiredError(TokenValidationError):
    """Raised when an authentication token has expired."""

    def __init__(self, token_type: AuthenticationTokenType) -> None:
        self.token_type = token_type
        AuthenticationError.__init__(self, f"Expired {token_type} token")


class RefreshTokenReuseError(TokenValidationError):
    """Raised when a rotated refresh token is presented again."""

    def __init__(self) -> None:
        self.token_type: AuthenticationTokenType = "refresh"
        AuthenticationError.__init__(self, "Refresh token reuse detected")


class UserAlreadyExistsError(Exception):
    """Raised when an email is already registered."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__("A user with this email already exists")


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
