import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.exceptions import RedisError

from expense_api.api.exception_handlers import (
    authentication_error_handler,
    expense_not_found_handler,
    expense_reference_not_found_handler,
    lookup_value_already_exists_handler,
    user_already_exists_handler,
)
from expense_api.api.router import api_router
from expense_api.cache import create_redis_client
from expense_api.core.config import get_settings
from expense_api.db.session import engine
from expense_api.exceptions import (
    AuthenticationError,
    CategoryAlreadyExistsError,
    ExpenseNotFoundError,
    ExpenseReferenceNotFoundError,
    PaymentMethodAlreadyExistsError,
    UserAlreadyExistsError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client = create_redis_client(get_settings())
    app.state.redis_client = redis_client
    try:
        try:
            await redis_client.ping()
        except RedisError:
            logger.warning(
                "Redis is unavailable during startup; cache will use PostgreSQL "
                "fallback",
                exc_info=True,
            )
        yield
    finally:
        try:
            await redis_client.aclose()
        finally:
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
    app.add_exception_handler(
        CategoryAlreadyExistsError,
        lookup_value_already_exists_handler,
    )
    app.add_exception_handler(
        PaymentMethodAlreadyExistsError,
        lookup_value_already_exists_handler,
    )
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
    app.include_router(api_router)
    return app
