import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://expense_test:password@localhost:5432/expense_test",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-with-at-least-32-characters",
)
os.environ.setdefault("COOKIE_SECURE", "true")
