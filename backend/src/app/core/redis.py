from __future__ import annotations

import json
from collections.abc import MutableMapping
from datetime import datetime
from typing import Any, Protocol, cast

import redis

from app.core.config import Settings, get_settings


class RedisLike(Protocol):
    def setex(self, name: str, time: int, value: str) -> bool: ...
    def get(self, name: str) -> str | bytes | None: ...
    def delete(self, name: str) -> int: ...
    def expire(self, name: str, time: int) -> bool: ...


class InMemoryRedis:
    def __init__(self) -> None:
        self._values: MutableMapping[str, str] = {}

    def setex(self, name: str, time: int, value: str) -> bool:
        self._values[name] = value
        return True

    def get(self, name: str) -> str | bytes | None:
        return self._values.get(name)

    def delete(self, name: str) -> int:
        return 1 if self._values.pop(name, None) is not None else 0

    def expire(self, name: str, time: int) -> bool:
        return name in self._values


def create_redis_client(settings: Settings | None = None) -> RedisLike:
    app_settings = settings or get_settings()
    from_url = cast(Any, redis.from_url)
    return cast(RedisLike, from_url(app_settings.redis_url, decode_responses=True))


def encode_json(value: dict[str, str]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def decode_json(raw_value: str | bytes | None) -> dict[str, str] | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")
    return cast(dict[str, str], json.loads(raw_value))


def serialize_datetime(value: datetime) -> str:
    return value.isoformat()
