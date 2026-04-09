from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import ScheduledPayment, ScheduledPaymentFrequency


class ScheduledPaymentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        workspace_id: UUID,
        amount_minor: int,
        currency: str,
        category_id: UUID | None,
        description: str | None,
        frequency: ScheduledPaymentFrequency,
        next_due_date: datetime,
    ) -> ScheduledPayment:
        scheduled_payment = ScheduledPayment(
            workspace_id=workspace_id,
            amount_minor=amount_minor,
            currency=currency,
            category_id=category_id,
            description=description,
            frequency=frequency,
            next_due_date=next_due_date,
        )
        self._session.add(scheduled_payment)
        self._session.flush()
        self._session.refresh(scheduled_payment)
        return scheduled_payment

    def list_by_workspace(self, *, workspace_id: UUID) -> list[ScheduledPayment]:
        statement = self._base_query().where(ScheduledPayment.workspace_id == workspace_id)
        statement = statement.order_by(ScheduledPayment.next_due_date.asc())
        return list(self._session.scalars(statement).all())

    def get_by_id(
        self, *, workspace_id: UUID, scheduled_payment_id: UUID
    ) -> ScheduledPayment | None:
        statement = self._base_query().where(
            ScheduledPayment.workspace_id == workspace_id,
            ScheduledPayment.id == scheduled_payment_id,
        )
        return self._session.scalar(statement)

    def update(
        self,
        scheduled_payment: ScheduledPayment,
        *,
        amount_minor: int,
        currency: str,
        category_id: UUID | None,
        description: str | None,
        frequency: ScheduledPaymentFrequency,
        next_due_date: datetime,
        is_active: bool,
    ) -> ScheduledPayment:
        scheduled_payment.amount_minor = amount_minor
        scheduled_payment.currency = currency
        scheduled_payment.category_id = category_id
        scheduled_payment.description = description
        scheduled_payment.frequency = frequency
        scheduled_payment.next_due_date = next_due_date
        scheduled_payment.is_active = is_active
        self._session.add(scheduled_payment)
        self._session.flush()
        self._session.refresh(scheduled_payment)
        return scheduled_payment

    def delete(self, scheduled_payment: ScheduledPayment) -> None:
        self._session.delete(scheduled_payment)
        self._session.flush()

    @staticmethod
    def _base_query() -> Select[tuple[ScheduledPayment]]:
        return select(ScheduledPayment).options(joinedload(ScheduledPayment.workspace))
