from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Account, AccountType


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        workspace_id: UUID,
        name: str,
        account_type: AccountType,
        currency: str,
        initial_balance_minor: int,
        description: str | None,
    ) -> Account:
        account = Account(
            workspace_id=workspace_id,
            name=name,
            type=account_type,
            currency=currency,
            initial_balance_minor=initial_balance_minor,
            current_balance_minor=initial_balance_minor,
            description=description,
        )
        self._session.add(account)
        self._session.flush()
        self._session.refresh(account)
        return account

    def list_by_workspace(
        self, *, workspace_id: UUID, user_id: UUID, include_archived: bool
    ) -> list[Account]:
        statement = self._base_query().where(Account.workspace_id == workspace_id)
        if not include_archived:
            statement = statement.where(Account.archived_at.is_(None))
        statement = statement.where(
            (Account.owner_user_id.is_(None)) | (Account.owner_user_id == user_id)
        )
        statement = statement.order_by(Account.created_at.asc())
        return list(self._session.scalars(statement).all())

    def get_by_id(self, *, workspace_id: UUID, account_id: UUID) -> Account | None:
        statement = self._base_query().where(
            Account.workspace_id == workspace_id,
            Account.id == account_id,
        )
        return self._session.scalar(statement)

    def list_by_ids(self, *, workspace_id: UUID, account_ids: set[UUID]) -> list[Account]:
        if not account_ids:
            return []

        statement = self._base_query().where(
            Account.workspace_id == workspace_id,
            Account.id.in_(account_ids),
        )
        return list(self._session.scalars(statement).all())

    def get_active_by_name(
        self,
        *,
        workspace_id: UUID,
        name: str,
        exclude_account_id: UUID | None = None,
    ) -> Account | None:
        statement = self._base_query().where(
            Account.workspace_id == workspace_id,
            Account.archived_at.is_(None),
            func.lower(Account.name) == name.lower(),
        )
        if exclude_account_id is not None:
            statement = statement.where(Account.id != exclude_account_id)
        return self._session.scalar(statement)

    def update(
        self,
        account: Account,
        *,
        name: str,
        account_type: AccountType,
        currency: str,
        initial_balance_minor: int,
        current_balance_minor: int,
        description: str | None,
    ) -> Account:
        account.name = name
        account.type = account_type
        account.currency = currency
        account.initial_balance_minor = initial_balance_minor
        account.current_balance_minor = current_balance_minor
        account.description = description
        self._session.add(account)
        self._session.flush()
        self._session.refresh(account)
        return account

    def archive(self, account: Account, *, archived_at: datetime) -> Account:
        account.archived_at = archived_at
        self._session.add(account)
        self._session.flush()
        self._session.refresh(account)
        return account

    @staticmethod
    def _base_query() -> Select[tuple[Account]]:
        return select(Account).options(joinedload(Account.workspace))
