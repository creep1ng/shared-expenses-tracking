from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Transaction, TransactionType


class NetBalanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def compute_pairwise_net(self, *, workspace_id: UUID) -> dict[tuple[UUID, UUID, str], int]:
        """Compute net pairwise balances for a workspace.

        Returns a dict mapping (debtor_id, creditor_id, currency) -> amount_minor.
        Positive values mean debtor owes creditor.
        """
        statement = (
            select(Transaction)
            .where(
                Transaction.workspace_id == workspace_id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.split_config.is_not(None),
                Transaction.paid_by_user_id.is_not(None),
            )
            .order_by(Transaction.occurred_at.asc())
        )
        transactions = list(self._session.scalars(statement).all())

        # Accumulate gross debts: (debtor, creditor, currency) -> amount
        gross: dict[tuple[UUID, UUID, str], int] = {}
        for txn in transactions:
            payer = txn.paid_by_user_id
            if payer is None or txn.split_config is None:
                continue

            config: dict[str, Any] = txn.split_config
            split_type = str(config.get("type", "equal"))
            values = config.get("values")
            typed_values: dict[str, Any] | None = values if isinstance(values, dict) else None
            amount = txn.amount_minor
            currency = txn.currency

            shares = self._compute_shares(
                split_type=split_type,
                values=typed_values,
                amount_minor=amount,
                payer_id=payer,
            )

            for participant_id, share_amount in shares.items():
                if participant_id == payer:
                    continue  # Payer doesn't owe themselves
                if share_amount <= 0:
                    continue
                key = (participant_id, payer, currency)
                gross[key] = gross.get(key, 0) + share_amount

        # Net out bilateral debts
        net: dict[tuple[UUID, UUID, str], int] = {}
        processed_pairs: set[tuple[UUID, UUID, str]] = set()

        for (debtor, creditor, currency), amount in gross.items():
            canonical = (debtor, creditor, currency)
            reverse = (creditor, debtor, currency)

            if (creditor, debtor, currency) in processed_pairs:
                continue
            processed_pairs.add(canonical)
            processed_pairs.add(reverse)

            reverse_amount = gross.get(reverse, 0)
            if amount > reverse_amount:
                net[canonical] = amount - reverse_amount
            elif reverse_amount > amount:
                net[reverse] = reverse_amount - amount
            # If equal, no net debt

        return net

    @staticmethod
    def _compute_shares(
        *,
        split_type: str,
        values: dict[str, Any] | None,
        amount_minor: int,
        payer_id: UUID,
    ) -> dict[UUID, int]:
        """Compute each participant's share of the transaction amount."""
        if split_type == "equal":
            if values:
                participant_ids = [UUID(uid) for uid in values.keys()]
            else:
                participant_ids = [payer_id]

            n = len(participant_ids)
            if n == 0:
                return {payer_id: amount_minor}

            base_share = amount_minor // n
            remainder = amount_minor % n

            shares: dict[UUID, int] = {}
            for i, uid in enumerate(participant_ids):
                shares[uid] = base_share + (1 if i < remainder else 0)
            return shares

        if split_type == "percentage":
            if not values:
                return {payer_id: amount_minor}
            shares = {}
            for uid_str, pct in values.items():
                uid = UUID(uid_str)
                shares[uid] = round(amount_minor * int(pct) / 100)
            return shares

        if split_type == "exact":
            if not values:
                return {payer_id: amount_minor}
            shares = {}
            for uid_str, amt in values.items():
                uid = UUID(uid_str)
                shares[uid] = int(amt)
            return shares

        return {payer_id: amount_minor}
