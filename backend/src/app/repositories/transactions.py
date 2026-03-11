from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Transaction, TransactionType


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        workspace_id: UUID,
        transaction_type: TransactionType,
        source_account_id: UUID | None,
        destination_account_id: UUID | None,
        category_id: UUID | None,
        paid_by_user_id: UUID | None,
        amount_minor: int,
        currency: str,
        description: str | None,
        occurred_at: datetime,
        split_config: dict[str, object] | None,
    ) -> Transaction:
        transaction = Transaction(
            workspace_id=workspace_id,
            type=transaction_type,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            category_id=category_id,
            paid_by_user_id=paid_by_user_id,
            amount_minor=amount_minor,
            currency=currency,
            description=description,
            occurred_at=occurred_at,
            split_config=split_config,
        )
        self._session.add(transaction)
        self._session.flush()
        self._session.refresh(transaction)
        return transaction

    def list_by_workspace(self, *, workspace_id: UUID) -> list[Transaction]:
        statement = (
            self._base_query()
            .where(Transaction.workspace_id == workspace_id)
            .order_by(Transaction.occurred_at.desc(), Transaction.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def get_by_id(self, *, workspace_id: UUID, transaction_id: UUID) -> Transaction | None:
        statement = self._base_query().where(
            Transaction.workspace_id == workspace_id,
            Transaction.id == transaction_id,
        )
        return self._session.scalar(statement)

    def update(
        self,
        transaction: Transaction,
        *,
        transaction_type: TransactionType,
        source_account_id: UUID | None,
        destination_account_id: UUID | None,
        category_id: UUID | None,
        paid_by_user_id: UUID | None,
        amount_minor: int,
        currency: str,
        description: str | None,
        occurred_at: datetime,
        split_config: dict[str, object] | None,
    ) -> Transaction:
        transaction.type = transaction_type
        transaction.source_account_id = source_account_id
        transaction.destination_account_id = destination_account_id
        transaction.category_id = category_id
        transaction.paid_by_user_id = paid_by_user_id
        transaction.amount_minor = amount_minor
        transaction.currency = currency
        transaction.description = description
        transaction.occurred_at = occurred_at
        transaction.split_config = split_config
        self._session.add(transaction)
        self._session.flush()
        self._session.refresh(transaction)
        return transaction

    def update_receipt_url(
        self, transaction: Transaction, *, receipt_url: str | None
    ) -> Transaction:
        transaction.receipt_url = receipt_url
        self._session.add(transaction)
        self._session.flush()
        self._session.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self._session.delete(transaction)
        self._session.flush()

    def sum_incoming_amounts_by_account(
        self,
        *,
        workspace_id: UUID,
        account_ids: Sequence[UUID],
    ) -> dict[UUID, int]:
        if not account_ids:
            return {}

        statement = (
            select(
                Transaction.destination_account_id,
                func.coalesce(func.sum(Transaction.amount_minor), 0),
            )
            .where(
                Transaction.workspace_id == workspace_id,
                Transaction.destination_account_id.in_(account_ids),
                Transaction.type.in_((TransactionType.INCOME, TransactionType.TRANSFER)),
            )
            .group_by(Transaction.destination_account_id)
        )
        return {
            account_id: int(total)
            for account_id, total in self._session.execute(statement).all()
            if account_id is not None
        }

    def sum_outgoing_amounts_by_account(
        self,
        *,
        workspace_id: UUID,
        account_ids: Sequence[UUID],
    ) -> dict[UUID, int]:
        if not account_ids:
            return {}

        statement = (
            select(
                Transaction.source_account_id,
                func.coalesce(func.sum(Transaction.amount_minor), 0),
            )
            .where(
                Transaction.workspace_id == workspace_id,
                Transaction.source_account_id.in_(account_ids),
                Transaction.type.in_((TransactionType.EXPENSE, TransactionType.TRANSFER)),
            )
            .group_by(Transaction.source_account_id)
        )
        return {
            account_id: int(total)
            for account_id, total in self._session.execute(statement).all()
            if account_id is not None
        }

    @staticmethod
    def _base_query() -> Select[tuple[Transaction]]:
        return select(Transaction).options(
            joinedload(Transaction.workspace),
            joinedload(Transaction.source_account),
            joinedload(Transaction.destination_account),
            joinedload(Transaction.category),
            joinedload(Transaction.paid_by_user),
        )
