from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import ScheduledPayment, ScheduledPaymentFrequency, User
from app.repositories.scheduled_payments import ScheduledPaymentRepository
from app.services.workspaces import WorkspaceService


class ScheduledPaymentService:
    def __init__(self, session: Session, workspace_service: WorkspaceService) -> None:
        self._session = session
        self._workspace_service = workspace_service
        self._scheduled_payments = ScheduledPaymentRepository(session)

    def create_scheduled_payment(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        amount_minor: int,
        currency: str,
        category_id: UUID | None,
        description: str | None,
        frequency: ScheduledPaymentFrequency,
        next_due_date: datetime,
    ) -> ScheduledPayment:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )

        normalized_currency = self._normalize_currency(currency)
        normalized_description = self._normalize_description(description)
        normalized_next_due_date = self._normalize_next_due_date(next_due_date)

        scheduled_payment = self._scheduled_payments.create(
            workspace_id=workspace_id,
            amount_minor=amount_minor,
            currency=normalized_currency,
            category_id=category_id,
            description=normalized_description,
            frequency=frequency,
            next_due_date=normalized_next_due_date,
        )

        self._session.commit()
        return scheduled_payment

    def list_scheduled_payments(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
    ) -> list[ScheduledPayment]:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        return self._scheduled_payments.list_by_workspace(workspace_id=workspace_id)

    def update_scheduled_payment(
        self,
        *,
        workspace_id: UUID,
        scheduled_payment_id: UUID,
        current_user: User,
        updates: dict[str, Any],
    ) -> ScheduledPayment:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )

        scheduled_payment = self._get_scheduled_payment_or_404(
            workspace_id=workspace_id,
            scheduled_payment_id=scheduled_payment_id,
        )

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided.",
            )

        updated_amount = updates.get("amount_minor", scheduled_payment.amount_minor)
        updated_currency = (
            self._normalize_currency(str(updates["currency"]))
            if "currency" in updates
            else scheduled_payment.currency
        )
        updated_category_id = updates.get("category_id", scheduled_payment.category_id)
        updated_description = (
            self._normalize_description(updates.get("description"))
            if "description" in updates
            else scheduled_payment.description
        )
        updated_frequency = (
            ScheduledPaymentFrequency(updates["frequency"])
            if "frequency" in updates
            else scheduled_payment.frequency
        )
        updated_next_due_date = (
            self._normalize_next_due_date(updates["next_due_date"])
            if "next_due_date" in updates
            else scheduled_payment.next_due_date
        )
        updated_is_active = updates.get("is_active", scheduled_payment.is_active)

        updated_scheduled_payment = self._scheduled_payments.update(
            scheduled_payment,
            amount_minor=updated_amount,
            currency=updated_currency,
            category_id=updated_category_id,
            description=updated_description,
            frequency=updated_frequency,
            next_due_date=updated_next_due_date,
            is_active=updated_is_active,
        )

        self._session.commit()
        return updated_scheduled_payment

    def delete_scheduled_payment(
        self,
        *,
        workspace_id: UUID,
        scheduled_payment_id: UUID,
        current_user: User,
    ) -> None:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )

        scheduled_payment = self._get_scheduled_payment_or_404(
            workspace_id=workspace_id,
            scheduled_payment_id=scheduled_payment_id,
        )

        self._scheduled_payments.delete(scheduled_payment)
        self._session.commit()

    def _get_scheduled_payment_or_404(
        self, *, workspace_id: UUID, scheduled_payment_id: UUID
    ) -> ScheduledPayment:
        scheduled_payment = self._scheduled_payments.get_by_id(
            workspace_id=workspace_id,
            scheduled_payment_id=scheduled_payment_id,
        )
        if scheduled_payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled payment not found.",
            )
        return scheduled_payment

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
    def _normalize_next_due_date(next_due_date: datetime) -> datetime:
        if next_due_date < utc_now():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Next due date cannot be in the past.",
            )
        return next_due_date
