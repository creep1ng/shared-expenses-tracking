from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.accounts import get_account_service
from app.api.dependencies.auth import get_current_user
from app.db.models import Account, User
from app.schemas.accounts import (
    AccountCreateRequest,
    AccountListResponse,
    AccountResponse,
    AccountUpdateRequest,
)
from app.services.accounts import AccountService

router = APIRouter(prefix="/workspaces/{workspace_id}/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    workspace_id: UUID,
    payload: AccountCreateRequest,
    current_user: User = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    account = account_service.create_account(
        workspace_id=workspace_id,
        current_user=current_user,
        name=payload.name,
        account_type=payload.type,
        currency=payload.currency,
        initial_balance_minor=payload.initial_balance_minor,
        description=payload.description,
    )
    return _build_account_response(account)


@router.get("", response_model=AccountListResponse)
def list_accounts(
    workspace_id: UUID,
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
) -> AccountListResponse:
    accounts = account_service.list_accounts(
        workspace_id=workspace_id,
        current_user=current_user,
        include_archived=include_archived,
    )
    return AccountListResponse(accounts=[_build_account_response(account) for account in accounts])


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    workspace_id: UUID,
    account_id: UUID,
    payload: AccountUpdateRequest,
    current_user: User = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    account = account_service.update_account(
        workspace_id=workspace_id,
        account_id=account_id,
        current_user=current_user,
        updates=payload.model_dump(exclude_unset=True),
    )
    return _build_account_response(account)


@router.post("/{account_id}/archive", response_model=AccountResponse)
def archive_account(
    workspace_id: UUID,
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    account = account_service.archive_account(
        workspace_id=workspace_id,
        account_id=account_id,
        current_user=current_user,
    )
    return _build_account_response(account)


def _build_account_response(account: Account) -> AccountResponse:
    return AccountResponse.model_validate(account)
