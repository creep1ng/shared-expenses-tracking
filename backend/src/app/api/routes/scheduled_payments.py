from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.scheduled_payments import get_scheduled_payment_service
from app.db.models import ScheduledPayment, User
from app.schemas.scheduled_payments import (
    ScheduledPaymentCreateRequest,
    ScheduledPaymentListResponse,
    ScheduledPaymentResponse,
    ScheduledPaymentUpdateRequest,
)
from app.services.scheduled_payments import ScheduledPaymentService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/scheduled-payments", tags=["scheduled-payments"]
)


@router.post("", response_model=ScheduledPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_payment(
    workspace_id: UUID,
    payload: ScheduledPaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    scheduled_payment_service: ScheduledPaymentService = Depends(get_scheduled_payment_service),
) -> ScheduledPaymentResponse:
    scheduled_payment = scheduled_payment_service.create_scheduled_payment(
        workspace_id=workspace_id,
        current_user=current_user,
        amount_minor=payload.amount_minor,
        currency=payload.currency,
        category_id=payload.category_id,
        description=payload.description,
        frequency=payload.frequency,
        next_due_date=payload.next_due_date,
    )
    return _build_scheduled_payment_response(scheduled_payment)


@router.get("", response_model=ScheduledPaymentListResponse)
def list_scheduled_payments(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    scheduled_payment_service: ScheduledPaymentService = Depends(get_scheduled_payment_service),
) -> ScheduledPaymentListResponse:
    scheduled_payments = scheduled_payment_service.list_scheduled_payments(
        workspace_id=workspace_id,
        current_user=current_user,
    )
    return ScheduledPaymentListResponse(
        scheduled_payments=[_build_scheduled_payment_response(sp) for sp in scheduled_payments]
    )


@router.patch("/{scheduled_payment_id}", response_model=ScheduledPaymentResponse)
def update_scheduled_payment(
    workspace_id: UUID,
    scheduled_payment_id: UUID,
    payload: ScheduledPaymentUpdateRequest,
    current_user: User = Depends(get_current_user),
    scheduled_payment_service: ScheduledPaymentService = Depends(get_scheduled_payment_service),
) -> ScheduledPaymentResponse:
    scheduled_payment = scheduled_payment_service.update_scheduled_payment(
        workspace_id=workspace_id,
        scheduled_payment_id=scheduled_payment_id,
        current_user=current_user,
        updates=payload.model_dump(exclude_unset=True),
    )
    return _build_scheduled_payment_response(scheduled_payment)


@router.delete("/{scheduled_payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_payment(
    workspace_id: UUID,
    scheduled_payment_id: UUID,
    current_user: User = Depends(get_current_user),
    scheduled_payment_service: ScheduledPaymentService = Depends(get_scheduled_payment_service),
) -> None:
    scheduled_payment_service.delete_scheduled_payment(
        workspace_id=workspace_id,
        scheduled_payment_id=scheduled_payment_id,
        current_user=current_user,
    )


def _build_scheduled_payment_response(
    scheduled_payment: ScheduledPayment,
) -> ScheduledPaymentResponse:
    return ScheduledPaymentResponse.model_validate(scheduled_payment)
