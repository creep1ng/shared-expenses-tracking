from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.workspaces import (
    get_workspace_member_access,
    get_workspace_service,
)
from app.db.models import User, WorkspaceInvitation, WorkspaceMember
from app.schemas.workspaces import (
    AcceptWorkspaceInvitationRequest,
    AcceptWorkspaceInvitationResponse,
    WorkspaceCreateRequest,
    WorkspaceInvitationCreateRequest,
    WorkspaceInvitationCreateResponse,
    WorkspaceInvitationResponse,
    WorkspaceInvitationsResponse,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspaceMembersResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.workspaces import WorkspaceAccess, WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    access = workspace_service.create_workspace(
        current_user=current_user,
        name=payload.name,
        workspace_type=payload.type,
    )
    return _build_workspace_response(access)


@router.get("", response_model=WorkspaceListResponse)
def list_workspaces(
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceListResponse:
    accesses = workspace_service.list_workspaces(current_user=current_user)
    return WorkspaceListResponse(
        workspaces=[_build_workspace_response(access) for access in accesses]
    )


@router.post("/invitations/accept", response_model=AcceptWorkspaceInvitationResponse)
def accept_workspace_invitation(
    payload: AcceptWorkspaceInvitationRequest,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> AcceptWorkspaceInvitationResponse:
    access = workspace_service.accept_invitation(token=payload.token, current_user=current_user)
    return AcceptWorkspaceInvitationResponse(workspace=_build_workspace_response(access))


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def read_workspace(
    access: WorkspaceAccess = Depends(get_workspace_member_access),
) -> WorkspaceResponse:
    return _build_workspace_response(access)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    access = workspace_service.update_workspace_name(
        workspace_id=workspace_id,
        current_user=current_user,
        name=payload.name,
    )
    return _build_workspace_response(access)


@router.get("/{workspace_id}/members", response_model=WorkspaceMembersResponse)
def list_workspace_members(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceMembersResponse:
    members = workspace_service.list_members(workspace_id=workspace_id, current_user=current_user)
    return WorkspaceMembersResponse(members=[_build_member_response(member) for member in members])


@router.post(
    "/{workspace_id}/invitations",
    response_model=WorkspaceInvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace_invitation(
    workspace_id: UUID,
    payload: WorkspaceInvitationCreateRequest,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceInvitationCreateResponse:
    result = workspace_service.create_invitation(
        workspace_id=workspace_id,
        current_user=current_user,
        invited_email=payload.email,
    )
    return WorkspaceInvitationCreateResponse(
        **_build_invitation_response(result.invitation).model_dump(),
        invitation_token=result.token,
    )


@router.get("/{workspace_id}/invitations", response_model=WorkspaceInvitationsResponse)
def list_workspace_invitations(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceInvitationsResponse:
    invitations = workspace_service.list_invitations(
        workspace_id=workspace_id,
        current_user=current_user,
    )
    return WorkspaceInvitationsResponse(
        invitations=[_build_invitation_response(invitation) for invitation in invitations]
    )


@router.post(
    "/{workspace_id}/invitations/{invitation_id}/revoke", response_model=WorkspaceInvitationResponse
)
def revoke_workspace_invitation(
    workspace_id: UUID,
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceInvitationResponse:
    invitation = workspace_service.revoke_invitation(
        workspace_id=workspace_id,
        invitation_id=invitation_id,
        current_user=current_user,
    )
    return _build_invitation_response(invitation)


def _build_workspace_response(access: WorkspaceAccess) -> WorkspaceResponse:
    workspace = access.workspace
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        type=workspace.type,
        created_by_user_id=workspace.created_by_user_id,
        current_user_role=access.membership.role,
        member_count=len(workspace.members),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def _build_member_response(member: WorkspaceMember) -> WorkspaceMemberResponse:
    return WorkspaceMemberResponse(
        user_id=member.user.id,
        email=member.user.email,
        is_active=member.user.is_active,
        role=member.role,
        joined_at=member.created_at,
    )


def _build_invitation_response(invitation: WorkspaceInvitation) -> WorkspaceInvitationResponse:
    return WorkspaceInvitationResponse.model_validate(invitation)
