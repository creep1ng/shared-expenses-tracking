from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db_session
from app.services.workspaces import WorkspaceAccess, WorkspaceService


def get_workspace_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> WorkspaceService:
    return WorkspaceService(session=session, settings=settings)


def get_workspace_member_access(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceAccess:
    return workspace_service.get_workspace_access(
        workspace_id=workspace_id,
        current_user=current_user,
    )


def get_workspace_owner_access(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceAccess:
    return workspace_service.get_owner_access(
        workspace_id=workspace_id,
        current_user=current_user,
    )
