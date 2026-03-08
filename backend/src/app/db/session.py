from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

_SESSION_FACTORIES: dict[str, sessionmaker[Session]] = {}


def create_engine_from_settings(settings: Settings | None = None) -> Engine:
    app_settings = settings or get_settings()
    return create_engine(
        app_settings.database_url,
        echo=app_settings.database_echo,
        pool_pre_ping=True,
    )


def create_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    app_settings = settings or get_settings()
    cache_key = app_settings.database_url

    if cache_key not in _SESSION_FACTORIES:
        engine = create_engine_from_settings(app_settings)
        _SESSION_FACTORIES[cache_key] = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    return _SESSION_FACTORIES[cache_key]


def get_db_session() -> Generator[Session]:
    session_factory = create_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
