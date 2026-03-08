from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title="Shared Expenses Tracking API",
        version="0.1.0",
        debug=app_settings.app_debug,
    )
    app.include_router(auth_router, prefix=app_settings.api_v1_prefix)
    app.include_router(health_router, prefix=app_settings.api_v1_prefix)

    return app


app: FastAPI | None = None


def get_app() -> FastAPI:
    global app
    if app is None:
        app = create_app()
    return app


app = get_app()
