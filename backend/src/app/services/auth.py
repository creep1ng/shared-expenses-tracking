from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.redis import RedisLike, decode_json, encode_json, serialize_datetime
from app.core.security import (
    generate_urlsafe_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.core.time import utc_now
from app.db.models import User
from app.repositories.auth import PasswordResetTokenRepository, UserRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SessionData:
    session_id: str
    user_id: UUID


@dataclass(frozen=True)
class PasswordResetRequestResult:
    token: str | None


class AuthService:
    def __init__(self, session: Session, redis_client: RedisLike, settings: Settings) -> None:
        self._session = session
        self._redis = redis_client
        self._settings = settings
        self._users = UserRepository(session)
        self._reset_tokens = PasswordResetTokenRepository(session)

    def sign_up(self, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        self._validate_password(password)

        if self._users.get_by_email(normalized_email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with that email already exists.",
            )

        user = self._users.create(
            email=normalized_email,
            password_hash=hash_password(password, self._settings).value,
        )
        self._session.commit()
        return user

    def sign_in(self, *, email: str, password: str) -> tuple[User, SessionData]:
        normalized_email = email.strip().lower()
        user = self._users.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash, self._settings):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user account is inactive.",
            )

        session_id = generate_urlsafe_token()
        self._redis.setex(
            self._session_key(session_id),
            self._settings.auth_session_ttl_seconds,
            encode_json({"user_id": str(user.id), "created_at": serialize_datetime(utc_now())}),
        )
        return user, SessionData(session_id=session_id, user_id=user.id)

    def sign_out(self, session_id: str | None) -> None:
        if session_id is None:
            return
        self._redis.delete(self._session_key(session_id))

    def get_current_user(self, session_id: str | None) -> User:
        if session_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )

        payload = decode_json(self._redis.get(self._session_key(session_id)))
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )

        user_id_raw = payload.get("user_id")
        if user_id_raw is None:
            self._redis.delete(self._session_key(session_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )

        user = self._users.get_by_id(UUID(user_id_raw))
        if user is None or not user.is_active:
            self._redis.delete(self._session_key(session_id))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated."
            )

        self._redis.expire(self._session_key(session_id), self._settings.auth_session_ttl_seconds)
        return user

    def request_password_reset(self, *, email: str) -> PasswordResetRequestResult:
        normalized_email = email.strip().lower()
        user = self._users.get_by_email(normalized_email)
        if user is None:
            return PasswordResetRequestResult(token=None)

        now = utc_now()
        token = generate_urlsafe_token(24)
        token_hash = hash_reset_token(token, self._settings)
        expires_at = now + timedelta(seconds=self._settings.auth_reset_token_ttl_seconds)

        self._reset_tokens.delete_expired(now)
        self._reset_tokens.revoke_for_user(user.id)
        self._reset_tokens.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        self._session.commit()

        logger.info(
            "Password reset token generated for user %s <%s>: %s",
            user.id,
            normalized_email,
            token,
        )

        return PasswordResetRequestResult(
            token=token if self._settings.auth_enable_dev_reset_token_response else None,
        )

    def confirm_password_reset(self, *, token: str, new_password: str) -> None:
        self._validate_password(new_password)
        now = utc_now()
        token_record = self._reset_tokens.get_active_by_hash(
            hash_reset_token(token, self._settings), now
        )

        if token_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token is invalid or expired.",
            )

        user = token_record.user
        self._users.update_password(
            user, password_hash=hash_password(new_password, self._settings).value
        )
        self._reset_tokens.consume(token_record, consumed_at=now)
        self._session.commit()

    def _validate_password(self, password: str) -> None:
        if len(password) < self._settings.auth_password_min_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Password must be at least "
                    f"{self._settings.auth_password_min_length} characters long."
                ),
            )

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"auth:session:{session_id}"
