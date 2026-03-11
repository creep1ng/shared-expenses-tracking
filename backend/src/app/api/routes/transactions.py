from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.transactions import get_transaction_service
from app.db.models import Transaction, User
from app.schemas.transactions import (
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.services.transactions import TransactionService

router = APIRouter(prefix="/workspaces/{workspace_id}/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    workspace_id: UUID,
    payload: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    transaction = transaction_service.create_transaction(
        workspace_id=workspace_id,
        current_user=current_user,
        payload=payload.model_dump(),
    )
    return _build_transaction_response(transaction)


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionListResponse:
    transactions = transaction_service.list_transactions(
        workspace_id=workspace_id,
        current_user=current_user,
    )
    return TransactionListResponse(
        transactions=[_build_transaction_response(transaction) for transaction in transactions]
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    workspace_id: UUID,
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    transaction = transaction_service.get_transaction(
        workspace_id=workspace_id,
        transaction_id=transaction_id,
        current_user=current_user,
    )
    return _build_transaction_response(transaction)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    workspace_id: UUID,
    transaction_id: UUID,
    payload: TransactionUpdateRequest,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    transaction = transaction_service.update_transaction(
        workspace_id=workspace_id,
        transaction_id=transaction_id,
        current_user=current_user,
        updates=payload.model_dump(exclude_unset=True),
    )
    return _build_transaction_response(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    workspace_id: UUID,
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> Response:
    transaction_service.delete_transaction(
        workspace_id=workspace_id,
        transaction_id=transaction_id,
        current_user=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _build_transaction_response(transaction: Transaction) -> TransactionResponse:
    return TransactionResponse.model_validate(transaction)
