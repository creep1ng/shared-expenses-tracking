from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import WorkspaceInvitationStatus, WorkspaceMemberRole, WorkspaceType


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: WorkspaceType


class WorkspaceUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: WorkspaceType
    created_by_user_id: UUID
    current_user_role: WorkspaceMemberRole
    member_count: int
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]


class WorkspaceMemberResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    is_active: bool
    role: WorkspaceMemberRole
    joined_at: datetime


class WorkspaceMembersResponse(BaseModel):
    members: list[WorkspaceMemberResponse]


class WorkspaceInvitationCreateRequest(BaseModel):
    email: EmailStr


class WorkspaceInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    invited_email: EmailStr
    invited_by_user_id: UUID
    accepted_by_user_id: UUID | None
    status: WorkspaceInvitationStatus
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkspaceInvitationCreateResponse(WorkspaceInvitationResponse):
    invitation_token: str


class WorkspaceInvitationsResponse(BaseModel):
    invitations: list[WorkspaceInvitationResponse]


class AcceptWorkspaceInvitationRequest(BaseModel):
    token: str = Field(min_length=20)


class AcceptWorkspaceInvitationResponse(BaseModel):
    workspace: WorkspaceResponse
