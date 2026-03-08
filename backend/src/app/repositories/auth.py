from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import PasswordResetToken, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self._session.scalar(statement)

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self._session.scalar(statement)

    def create(self, *, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user

    def update_password(self, user: User, *, password_hash: str) -> User:
        user.password_hash = password_hash
        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)
        return user


class PasswordResetTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._session.add(token)
        self._session.flush()
        self._session.refresh(token)
        return token

    def get_active_by_hash(self, token_hash: str, now: datetime) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.consumed_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        return self._session.scalar(statement)

    def consume(self, token: PasswordResetToken, *, consumed_at: datetime) -> PasswordResetToken:
        token.consumed_at = consumed_at
        self._session.add(token)
        self._session.flush()
        self._session.refresh(token)
        return token

    def revoke_for_user(self, user_id: UUID) -> None:
        statement = delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        self._session.execute(statement)

    def delete_expired(self, now: datetime) -> None:
        statement = delete(PasswordResetToken).where(PasswordResetToken.expires_at <= now)
        self._session.execute(statement)
