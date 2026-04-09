from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Account, AccountType, User
from app.repositories.accounts import AccountRepository
from app.services.workspaces import WorkspaceService


class AccountService:
    def __init__(self, session: Session, workspace_service: WorkspaceService) -> None:
        self._session = session
        self._workspace_service = workspace_service
        self._accounts = AccountRepository(session)

    def create_account(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        name: str,
        account_type: AccountType,
        currency: str,
        initial_balance_minor: int,
        description: str | None,
    ) -> Account:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        normalized_name = self._normalize_name(name)
        normalized_currency = self._normalize_currency(currency)
        normalized_description = self._normalize_description(description)
        self._ensure_active_name_available(workspace_id=workspace_id, name=normalized_name)

        try:
            account = self._accounts.create(
                workspace_id=workspace_id,
                name=normalized_name,
                account_type=account_type,
                currency=normalized_currency,
                initial_balance_minor=initial_balance_minor,
                description=normalized_description,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if self._is_duplicate_name_error(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active account with that name already exists in this workspace.",
                ) from exc
            raise

        return account

    def list_accounts(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        include_archived: bool,
    ) -> list[Account]:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        return self._accounts.list_by_workspace(
            workspace_id=workspace_id,
            user_id=current_user.id,
            include_archived=include_archived,
        )

    def update_account(
        self,
        *,
        workspace_id: UUID,
        account_id: UUID,
        current_user: User,
        updates: dict[str, Any],
    ) -> Account:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        account = self._get_account_or_404(workspace_id=workspace_id, account_id=account_id)
        if account.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Archived accounts cannot be updated.",
            )

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided.",
            )

        updated_name = (
            self._normalize_name(str(updates["name"])) if "name" in updates else account.name
        )
        updated_currency = (
            self._normalize_currency(str(updates["currency"]))
            if "currency" in updates
            else account.currency
        )
        updated_description = (
            self._normalize_description(updates.get("description"))
            if "description" in updates
            else account.description
        )
        updated_initial_balance_minor = (
            int(updates["initial_balance_minor"])
            if "initial_balance_minor" in updates
            else account.initial_balance_minor
        )
        updated_type = AccountType(updates["type"]) if "type" in updates else account.type
        updated_current_balance_minor = account.current_balance_minor + (
            updated_initial_balance_minor - account.initial_balance_minor
        )
        self._ensure_active_name_available(
            workspace_id=workspace_id,
            name=updated_name,
            exclude_account_id=account.id,
        )

        try:
            updated_account = self._accounts.update(
                account,
                name=updated_name,
                account_type=updated_type,
                currency=updated_currency,
                initial_balance_minor=updated_initial_balance_minor,
                current_balance_minor=updated_current_balance_minor,
                description=updated_description,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if self._is_duplicate_name_error(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An active account with that name already exists in this workspace.",
                ) from exc
            raise

        return updated_account

    def archive_account(
        self,
        *,
        workspace_id: UUID,
        account_id: UUID,
        current_user: User,
    ) -> Account:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        account = self._get_account_or_404(workspace_id=workspace_id, account_id=account_id)
        if account.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account has already been archived.",
            )

        archived_account = self._accounts.archive(account, archived_at=utc_now())
        self._session.commit()
        return archived_account

    def _get_account_or_404(self, *, workspace_id: UUID, account_id: UUID) -> Account:
        account = self._accounts.get_by_id(workspace_id=workspace_id, account_id=account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found.",
            )
        return account

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized_name = name.strip()
        if normalized_name == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Account name must not be empty.",
            )
        return normalized_name

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        normalized_currency = currency.strip().upper()
        if len(normalized_currency) != 3 or not normalized_currency.isalpha():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Currency must be a 3-letter ISO code.",
            )
        return normalized_currency

    @staticmethod
    def _normalize_description(description: str | None) -> str | None:
        if description is None:
            return None
        normalized_description = description.strip()
        return normalized_description or None

    def _ensure_active_name_available(
        self,
        *,
        workspace_id: UUID,
        name: str,
        exclude_account_id: UUID | None = None,
    ) -> None:
        duplicate_account = self._accounts.get_active_by_name(
            workspace_id=workspace_id,
            name=name,
            exclude_account_id=exclude_account_id,
        )
        if duplicate_account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active account with that name already exists in this workspace.",
            )

    @staticmethod
    def _is_duplicate_name_error(exc: IntegrityError) -> bool:
        return "uq_accounts_workspace_id_active_name" in str(exc.orig)
