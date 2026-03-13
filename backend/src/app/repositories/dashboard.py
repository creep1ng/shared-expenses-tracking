from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Account, Transaction, TransactionType


@dataclass(frozen=True)
class AccountCurrencyBalanceTotal:
    currency: str
    amount_minor: int


@dataclass(frozen=True)
class AnalyticsCurrencyTotal:
    currency: str
    transaction_type: TransactionType
    amount_minor: int


class DashboardRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active_account_balance_totals(
        self, *, workspace_id: UUID
    ) -> list[AccountCurrencyBalanceTotal]:
        statement = (
            select(Account.currency, func.coalesce(func.sum(Account.current_balance_minor), 0))
            .where(
                Account.workspace_id == workspace_id,
                Account.archived_at.is_(None),
            )
            .group_by(Account.currency)
            .order_by(Account.currency.asc())
        )

        return [
            AccountCurrencyBalanceTotal(currency=currency, amount_minor=int(amount_minor))
            for currency, amount_minor in self._session.execute(statement).all()
        ]

    def list_period_analytics_totals(
        self,
        *,
        workspace_id: UUID,
        start_at: datetime,
        end_at_exclusive: datetime,
    ) -> list[AnalyticsCurrencyTotal]:
        statement = (
            select(
                Transaction.currency,
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount_minor), 0),
            )
            .where(
                Transaction.workspace_id == workspace_id,
                Transaction.occurred_at >= start_at,
                Transaction.occurred_at < end_at_exclusive,
                Transaction.type.in_((TransactionType.INCOME, TransactionType.EXPENSE)),
            )
            .group_by(Transaction.currency, Transaction.type)
            .order_by(Transaction.currency.asc(), Transaction.type.asc())
        )

        return [
            AnalyticsCurrencyTotal(
                currency=currency,
                transaction_type=transaction_type,
                amount_minor=int(amount_minor),
            )
            for currency, transaction_type, amount_minor in self._session.execute(statement).all()
        ]
