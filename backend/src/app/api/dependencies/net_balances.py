from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.workspaces import get_workspace_service
from app.db.session import get_db_session
from app.services.net_balances import NetBalanceService
from app.services.workspaces import WorkspaceService


def get_net_balance_service(
    session: Session = Depends(get_db_session),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> NetBalanceService:
    return NetBalanceService(
        session=session,
        workspace_service=workspace_service,
    )
