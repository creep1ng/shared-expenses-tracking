from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.redis import InMemoryRedis, RedisLike, create_redis_client
from app.db.models import User
from app.db.session import get_db_session
from app.services.auth import AuthService

_TEST_REDIS = InMemoryRedis()


def get_redis_client(settings: Settings = Depends(get_settings)) -> RedisLike:
    if settings.app_env == "test":
        return _TEST_REDIS
    return create_redis_client(settings)


def get_auth_service(
    session: Session = Depends(get_db_session),
    redis_client: RedisLike = Depends(get_redis_client),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session=session, redis_client=redis_client, settings=settings)


def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> User:
    session_id = request.cookies.get(settings.auth_cookie_name)
    return auth_service.get_current_user(session_id)
