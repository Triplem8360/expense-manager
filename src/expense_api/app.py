from fastapi import FastAPI

from expense_api.api.exception_handlers import expense_not_found_handler
from expense_api.api.router import api_router
from expense_api.core.config import get_settings
from expense_api.exceptions import ExpenseNotFoundError
from expense_api.repositories import ExpenseRepository


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )
    app.state.expense_repository = ExpenseRepository()
    app.add_exception_handler(ExpenseNotFoundError, expense_not_found_handler)
    app.include_router(api_router)
    return app
