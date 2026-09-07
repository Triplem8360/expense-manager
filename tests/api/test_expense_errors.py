from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from expense_api.api.dependencies import get_current_user, get_expense_service
from expense_api.app import create_app
from expense_api.repositories import ExpenseRepository
from expense_api.services import ExpenseService

MISSING_EXPENSE_ID = 999_999


@pytest.fixture
def repository() -> AsyncMock:
    repository = AsyncMock(spec=ExpenseRepository)
    repository.get_by_id.return_value = None
    repository.delete.return_value = False
    repository.list_page.return_value = ([], 0)
    return repository


@pytest.fixture
def app(repository: AsyncMock) -> FastAPI:
    app = create_app()
    service = ExpenseService(repository)

    def override_expense_service() -> ExpenseService:
        return service

    def override_current_user() -> object:
        return object()

    app.dependency_overrides[get_expense_service] = override_expense_service
    app.dependency_overrides[get_current_user] = override_current_user
    return app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_get_missing_expense_returns_structured_404(
    client: TestClient,
    repository: AsyncMock,
) -> None:
    response = client.get(
        f"/api/v1/expenses/{MISSING_EXPENSE_ID}",
        params={"lang": "en"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "status": status.HTTP_404_NOT_FOUND,
        "message": f"Expense {MISSING_EXPENSE_ID} was not found",
    }
    assert response.headers["Content-Language"] == "en"
    repository.get_by_id.assert_awaited_once_with(MISSING_EXPENSE_ID)


def test_authentication_error_uses_shared_error_schema() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/expenses", params={"lang": "en"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "status": status.HTTP_401_UNAUTHORIZED,
        "message": "Access token is invalid",
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_delete_missing_expense_returns_structured_404(
    client: TestClient,
    repository: AsyncMock,
) -> None:
    response = client.delete(
        f"/api/v1/expenses/{MISSING_EXPENSE_ID}",
        params={"lang": "en"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "status": status.HTTP_404_NOT_FOUND,
        "message": f"Expense {MISSING_EXPENSE_ID} was not found",
    }
    repository.delete.assert_awaited_once_with(MISSING_EXPENSE_ID)


def test_list_expenses_succeeds_without_triggering_exception_handler(
    client: TestClient,
    repository: AsyncMock,
) -> None:
    response = client.get("/api/v1/expenses")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    repository.list_page.assert_awaited_once()


def test_delete_existing_expense_returns_empty_204_response(
    client: TestClient,
    repository: AsyncMock,
) -> None:
    repository.delete.return_value = True

    response = client.delete("/api/v1/expenses/1")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
    repository.delete.assert_awaited_once_with(1)
