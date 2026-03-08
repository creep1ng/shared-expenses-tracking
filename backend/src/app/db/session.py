from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import Settings, get_settings


def create_engine_from_settings(settings: Settings | None = None) -> Engine:
    app_settings = settings or get_settings()
    return create_engine(
        app_settings.database_url,
        echo=app_settings.database_echo,
        pool_pre_ping=True,
    )
