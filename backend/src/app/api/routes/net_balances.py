from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.net_balances import get_net_balance_service
from app.db.models import User
from app.schemas.net_balances import NetBalanceEntry, NetBalanceResponse, NetBalanceUserSummary
from app.services.net_balances import NetBalanceService

router = APIRouter(prefix="/workspaces/{workspace_id}/net-balances", tags=["net-balances"])


@router.get("", response_model=NetBalanceResponse)
def get_net_balances(
    workspace_id: UUID,
    user_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    net_balance_service: NetBalanceService = Depends(get_net_balance_service),
) -> NetBalanceResponse:
    entries = net_balance_service.get_net_balances(
        workspace_id=workspace_id,
        current_user=current_user,
        filter_user_id=user_id,
    )
    return NetBalanceResponse(
        balances=[
            NetBalanceEntry(
                debtor_id=entry.debtor_id,
                creditor_id=entry.creditor_id,
                amount_minor=entry.amount_minor,
                currency=entry.currency,
                debtor=NetBalanceUserSummary(id=entry.debtor_id, email=entry.debtor_email),
                creditor=NetBalanceUserSummary(id=entry.creditor_id, email=entry.creditor_email),
            )
            for entry in entries
        ]
    )
