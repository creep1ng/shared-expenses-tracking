from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    Category,
    CategoryType,
    Transaction,
    TransactionType,
    User,
    WorkspaceMember,
)
from app.repositories.accounts import AccountRepository
from app.repositories.categories import CategoryRepository
from app.repositories.transactions import TransactionRepository
from app.repositories.workspaces import WorkspaceMemberRepository
from app.services.workspaces import WorkspaceService


@dataclass(frozen=True)
class TransactionWriteData:
    transaction_type: TransactionType
    source_account_id: UUID | None
    destination_account_id: UUID | None
    category_id: UUID | None
    paid_by_user_id: UUID | None
    amount_minor: int
    currency: str
    description: str | None
    occurred_at: datetime
    split_config: dict[str, object] | None


class TransactionService:
    def __init__(self, session: Session, workspace_service: WorkspaceService) -> None:
        self._session = session
        self._workspace_service = workspace_service
        self._transactions = TransactionRepository(session)
        self._accounts = AccountRepository(session)
        self._categories = CategoryRepository(session)
        self._members = WorkspaceMemberRepository(session)

    def create_transaction(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        payload: dict[str, Any],
    ) -> Transaction:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        write_data = self._validate_write_data(workspace_id=workspace_id, payload=payload)

        transaction = self._transactions.create(
            workspace_id=workspace_id,
            transaction_type=write_data.transaction_type,
            source_account_id=write_data.source_account_id,
            destination_account_id=write_data.destination_account_id,
            category_id=write_data.category_id,
            paid_by_user_id=write_data.paid_by_user_id,
            amount_minor=write_data.amount_minor,
            currency=write_data.currency,
            description=write_data.description,
            occurred_at=write_data.occurred_at,
            split_config=write_data.split_config,
        )
        self._recompute_account_balances(
            workspace_id=workspace_id,
            account_ids=self._collect_account_ids(transaction=transaction),
        )
        self._session.commit()
        return self._get_transaction_or_404(
            workspace_id=workspace_id, transaction_id=transaction.id
        )

    def list_transactions(self, *, workspace_id: UUID, current_user: User) -> list[Transaction]:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        return self._transactions.list_by_workspace(workspace_id=workspace_id)

    def get_transaction(
        self,
        *,
        workspace_id: UUID,
        transaction_id: UUID,
        current_user: User,
    ) -> Transaction:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        return self._get_transaction_or_404(
            workspace_id=workspace_id, transaction_id=transaction_id
        )

    def update_transaction(
        self,
        *,
        workspace_id: UUID,
        transaction_id: UUID,
        current_user: User,
        updates: dict[str, Any],
    ) -> Transaction:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        transaction = self._get_transaction_or_404(
            workspace_id=workspace_id, transaction_id=transaction_id
        )
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided.",
            )

        merged_payload = {
            "type": updates["type"] if "type" in updates else transaction.type,
            "source_account_id": (
                updates["source_account_id"]
                if "source_account_id" in updates
                else transaction.source_account_id
            ),
            "destination_account_id": (
                updates["destination_account_id"]
                if "destination_account_id" in updates
                else transaction.destination_account_id
            ),
            "category_id": updates["category_id"]
            if "category_id" in updates
            else transaction.category_id,
            "paid_by_user_id": (
                updates["paid_by_user_id"]
                if "paid_by_user_id" in updates
                else transaction.paid_by_user_id
            ),
            "amount_minor": (
                updates["amount_minor"] if "amount_minor" in updates else transaction.amount_minor
            ),
            "currency": updates["currency"] if "currency" in updates else transaction.currency,
            "description": (
                updates["description"] if "description" in updates else transaction.description
            ),
            "occurred_at": (
                updates["occurred_at"] if "occurred_at" in updates else transaction.occurred_at
            ),
            "split_config": (
                updates["split_config"] if "split_config" in updates else transaction.split_config
            ),
        }
        write_data = self._validate_write_data(workspace_id=workspace_id, payload=merged_payload)
        affected_account_ids = self._collect_account_ids(transaction=transaction)

        updated_transaction = self._transactions.update(
            transaction,
            transaction_type=write_data.transaction_type,
            source_account_id=write_data.source_account_id,
            destination_account_id=write_data.destination_account_id,
            category_id=write_data.category_id,
            paid_by_user_id=write_data.paid_by_user_id,
            amount_minor=write_data.amount_minor,
            currency=write_data.currency,
            description=write_data.description,
            occurred_at=write_data.occurred_at,
            split_config=write_data.split_config,
        )
        affected_account_ids.update(self._collect_account_ids(transaction=updated_transaction))
        self._recompute_account_balances(
            workspace_id=workspace_id,
            account_ids=affected_account_ids,
        )
        self._session.commit()
        return self._get_transaction_or_404(
            workspace_id=workspace_id, transaction_id=transaction_id
        )

    def delete_transaction(
        self,
        *,
        workspace_id: UUID,
        transaction_id: UUID,
        current_user: User,
    ) -> None:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        transaction = self._get_transaction_or_404(
            workspace_id=workspace_id, transaction_id=transaction_id
        )
        affected_account_ids = self._collect_account_ids(transaction=transaction)
        self._transactions.delete(transaction)
        self._recompute_account_balances(
            workspace_id=workspace_id,
            account_ids=affected_account_ids,
        )
        self._session.commit()

    def _validate_write_data(
        self,
        *,
        workspace_id: UUID,
        payload: dict[str, Any],
    ) -> TransactionWriteData:
        transaction_type = TransactionType(payload["type"])
        source_account_id = payload.get("source_account_id")
        destination_account_id = payload.get("destination_account_id")
        category_id = payload.get("category_id")
        paid_by_user_id = payload.get("paid_by_user_id")
        amount_minor = int(payload["amount_minor"])
        if amount_minor <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="amount_minor must be greater than zero.",
            )
        currency = self._normalize_currency(str(payload["currency"]))
        description = self._normalize_description(payload.get("description"))
        occurred_at = self._normalize_occurred_at(payload["occurred_at"])
        split_config = self._normalize_split_config(payload.get("split_config"))

        account_ids = {
            account_id
            for account_id in (source_account_id, destination_account_id)
            if account_id is not None
        }
        accounts = {
            account.id: account
            for account in self._accounts.list_by_ids(
                workspace_id=workspace_id, account_ids=account_ids
            )
        }

        source_account = self._get_account_or_error(
            workspace_id=workspace_id,
            account_id=source_account_id,
            accounts=accounts,
            field_name="source_account_id",
        )
        destination_account = self._get_account_or_error(
            workspace_id=workspace_id,
            account_id=destination_account_id,
            accounts=accounts,
            field_name="destination_account_id",
        )
        category = self._get_category_or_error(
            workspace_id=workspace_id,
            category_id=category_id,
        )
        paid_by_member = self._get_workspace_member_or_error(
            workspace_id=workspace_id,
            user_id=paid_by_user_id,
        )

        self._validate_transaction_constraints(
            transaction_type=transaction_type,
            currency=currency,
            source_account=source_account,
            destination_account=destination_account,
            category=category,
        )

        return TransactionWriteData(
            transaction_type=transaction_type,
            source_account_id=source_account.id if source_account is not None else None,
            destination_account_id=destination_account.id
            if destination_account is not None
            else None,
            category_id=category.id if category is not None else None,
            paid_by_user_id=paid_by_member.user_id if paid_by_member is not None else None,
            amount_minor=amount_minor,
            currency=currency,
            description=description,
            occurred_at=occurred_at,
            split_config=split_config,
        )

    def _validate_transaction_constraints(
        self,
        *,
        transaction_type: TransactionType,
        currency: str,
        source_account: Account | None,
        destination_account: Account | None,
        category: Category | None,
    ) -> None:
        if transaction_type is TransactionType.INCOME:
            if destination_account is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Income transactions require destination_account_id.",
                )
            if source_account is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Income transactions must not include source_account_id.",
                )
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Income transactions require category_id.",
                )
            if category.type is not CategoryType.INCOME:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Income transactions require an income category.",
                )
            self._ensure_account_currency_matches(account=destination_account, currency=currency)
            return

        if transaction_type is TransactionType.EXPENSE:
            if source_account is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expense transactions require source_account_id.",
                )
            if destination_account is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expense transactions must not include destination_account_id.",
                )
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expense transactions require category_id.",
                )
            if category.type is not CategoryType.EXPENSE:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expense transactions require an expense category.",
                )
            self._ensure_account_currency_matches(account=source_account, currency=currency)
            return

        if source_account is None or destination_account is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Transfer transactions require source_account_id and destination_account_id."
                ),
            )
        if source_account.id == destination_account.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transfer transactions require different source and destination accounts.",
            )
        if category is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transfer transactions must not include category_id.",
            )
        self._ensure_account_currency_matches(account=source_account, currency=currency)
        self._ensure_account_currency_matches(account=destination_account, currency=currency)
        if source_account.currency != destination_account.currency:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transfer accounts must use the same currency.",
            )

    def _recompute_account_balances(self, *, workspace_id: UUID, account_ids: set[UUID]) -> None:
        if not account_ids:
            return

        accounts = self._accounts.list_by_ids(workspace_id=workspace_id, account_ids=account_ids)
        incoming_totals = self._transactions.sum_incoming_amounts_by_account(
            workspace_id=workspace_id,
            account_ids=[account.id for account in accounts],
        )
        outgoing_totals = self._transactions.sum_outgoing_amounts_by_account(
            workspace_id=workspace_id,
            account_ids=[account.id for account in accounts],
        )

        for account in accounts:
            account.current_balance_minor = (
                account.initial_balance_minor
                + incoming_totals.get(account.id, 0)
                - outgoing_totals.get(account.id, 0)
            )
            self._session.add(account)

        self._session.flush()

    def _get_transaction_or_404(self, *, workspace_id: UUID, transaction_id: UUID) -> Transaction:
        transaction = self._transactions.get_by_id(
            workspace_id=workspace_id,
            transaction_id=transaction_id,
        )
        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            )
        return transaction

    @staticmethod
    def _collect_account_ids(*, transaction: Transaction) -> set[UUID]:
        return {
            account_id
            for account_id in (transaction.source_account_id, transaction.destination_account_id)
            if account_id is not None
        }

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

    @staticmethod
    def _normalize_occurred_at(occurred_at: datetime) -> datetime:
        if occurred_at.tzinfo is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="occurred_at must be timezone-aware.",
            )
        return occurred_at.astimezone(UTC)

    @staticmethod
    def _normalize_split_config(split_config: dict[str, object] | None) -> dict[str, object] | None:
        return split_config

    @staticmethod
    def _ensure_account_currency_matches(*, account: Account, currency: str) -> None:
        if account.currency != currency:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transaction currency must match the linked account currency.",
            )

    @staticmethod
    def _ensure_account_is_active(*, account: Account, field_name: str) -> None:
        if account.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{field_name} references an archived account.",
            )

    @staticmethod
    def _ensure_category_is_active(*, category: Category) -> None:
        if category.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="category_id references an archived category.",
            )

    def _get_account_or_error(
        self,
        *,
        workspace_id: UUID,
        account_id: UUID | None,
        accounts: dict[UUID, Account],
        field_name: str,
    ) -> Account | None:
        if account_id is None:
            return None

        account = accounts.get(account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{field_name} references an account that was not found in this workspace.",
            )

        self._ensure_account_is_active(account=account, field_name=field_name)
        return account

    def _get_category_or_error(
        self, *, workspace_id: UUID, category_id: UUID | None
    ) -> Category | None:
        if category_id is None:
            return None

        category = self._categories.get_by_id(workspace_id=workspace_id, category_id=category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="category_id references a category that was not found in this workspace.",
            )

        self._ensure_category_is_active(category=category)
        return category

    def _get_workspace_member_or_error(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID | None,
    ) -> WorkspaceMember | None:
        if user_id is None:
            return None

        membership = self._members.get_for_user(workspace_id=workspace_id, user_id=user_id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="paid_by_user_id references a user who is not a member of this workspace.",
            )
        return membership
