from fastapi import FastAPI

from expense_api.api.router import api_router
from expense_api.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
    )
    app.include_router(api_router)
    return app
