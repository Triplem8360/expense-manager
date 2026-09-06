from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from expense_api.api.exception_handlers import (
    expense_not_found_handler,
    expense_reference_not_found_handler,
)
from expense_api.api.router import api_router
from expense_api.core.config import get_settings
from expense_api.db.session import engine
from expense_api.exceptions import (
    ExpenseNotFoundError,
    ExpenseReferenceNotFoundError,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.add_exception_handler(ExpenseNotFoundError, expense_not_found_handler)
    app.add_exception_handler(
        ExpenseReferenceNotFoundError,
        expense_reference_not_found_handler,
    )
    app.include_router(api_router)
    return app
