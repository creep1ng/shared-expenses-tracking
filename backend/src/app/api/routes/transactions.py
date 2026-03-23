from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.transactions import get_transaction_service
from app.db.models import Transaction, User
from app.schemas.transactions import (
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionReceiptUploadResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.services.transactions import (
    TransactionReceiptUpload,
    TransactionService,
)

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


@router.post(
    "/{transaction_id}/receipt",
    response_model=TransactionReceiptUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_transaction_receipt(
    workspace_id: UUID,
    transaction_id: UUID,
    receipt: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> TransactionReceiptUploadResponse:
    content = await _read_upload_file_chunked(
        receipt=receipt,
        max_size_bytes=transaction_service._settings.transaction_receipt_max_size_bytes,
    )
    transaction = transaction_service.upload_receipt(
        workspace_id=workspace_id,
        transaction_id=transaction_id,
        current_user=current_user,
        upload=TransactionReceiptUpload(
            content=content,
            content_type=receipt.content_type or "application/octet-stream",
        ),
    )
    return TransactionReceiptUploadResponse(receipt_url=transaction.receipt_url)


async def _read_upload_file_chunked(
    receipt: UploadFile,
    max_size_bytes: int,
    chunk_size: int = 64 * 1024,
) -> bytes:
    content = bytearray()
    while True:
        chunk = await receipt.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Receipt exceeds the 10 MB size limit.",
            )
    return bytes(content)


@router.get("/{transaction_id}/receipt/{filename}")
def get_transaction_receipt(
    workspace_id: UUID,
    transaction_id: UUID,
    filename: str,
    current_user: User = Depends(get_current_user),
    transaction_service: TransactionService = Depends(get_transaction_service),
) -> Response:
    receipt_content = transaction_service.get_receipt_content(
        workspace_id=workspace_id,
        transaction_id=transaction_id,
        filename=filename,
        current_user=current_user,
    )
    return Response(content=receipt_content.content, media_type=receipt_content.content_type)


def _build_transaction_response(transaction: Transaction) -> TransactionResponse:
    return TransactionResponse.model_validate(transaction)
