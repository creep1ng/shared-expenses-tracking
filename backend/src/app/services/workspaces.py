from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import generate_urlsafe_token, hash_workspace_invitation_token
from app.core.time import utc_now
from app.db.models import (
    User,
    Workspace,
    WorkspaceInvitation,
    WorkspaceInvitationStatus,
    WorkspaceMember,
    WorkspaceMemberRole,
    WorkspaceType,
)
from app.repositories.auth import UserRepository
from app.repositories.categories import CategoryRepository
from app.repositories.workspaces import (
    WorkspaceInvitationRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)


@dataclass(frozen=True)
class WorkspaceAccess:
    workspace: Workspace
    membership: WorkspaceMember


@dataclass(frozen=True)
class WorkspaceInvitationCreationResult:
    invitation: WorkspaceInvitation
    token: str


class WorkspaceService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._workspaces = WorkspaceRepository(session)
        self._members = WorkspaceMemberRepository(session)
        self._invitations = WorkspaceInvitationRepository(session)
        self._categories = CategoryRepository(session)

    def create_workspace(
        self, *, current_user: User, name: str, workspace_type: WorkspaceType
    ) -> WorkspaceAccess:
        normalized_name = self._normalize_workspace_name(name)
        workspace = self._workspaces.create(
            name=normalized_name,
            workspace_type=workspace_type,
            created_by_user_id=current_user.id,
        )
        membership = self._members.create(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=WorkspaceMemberRole.OWNER,
        )
        self._categories.ensure_default_categories_for_workspace(workspace_id=workspace.id)
        self._session.commit()
        return self.get_workspace_access(
            workspace_id=workspace.id, current_user=current_user, membership=membership
        )

    def list_workspaces(self, *, current_user: User) -> list[WorkspaceAccess]:
        memberships = self._members.list_for_user(user_id=current_user.id)
        return [WorkspaceAccess(workspace=item.workspace, membership=item) for item in memberships]

    def get_workspace_access(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        membership: WorkspaceMember | None = None,
    ) -> WorkspaceAccess:
        current_membership = membership or self._members.get_for_user(
            workspace_id=workspace_id,
            user_id=current_user.id,
        )
        if current_membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace.",
            )
        return WorkspaceAccess(
            workspace=current_membership.workspace,
            membership=current_membership,
        )

    def get_owner_access(self, *, workspace_id: UUID, current_user: User) -> WorkspaceAccess:
        access = self.get_workspace_access(workspace_id=workspace_id, current_user=current_user)
        if access.membership.role != WorkspaceMemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can perform this action.",
            )
        return access

    def update_workspace_name(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        name: str,
    ) -> WorkspaceAccess:
        access = self.get_owner_access(workspace_id=workspace_id, current_user=current_user)
        self._workspaces.update_name(access.workspace, name=self._normalize_workspace_name(name))
        self._session.commit()
        return self.get_workspace_access(workspace_id=workspace_id, current_user=current_user)

    def list_members(self, *, workspace_id: UUID, current_user: User) -> list[WorkspaceMember]:
        self.get_workspace_access(workspace_id=workspace_id, current_user=current_user)
        return self._members.list_by_workspace(workspace_id=workspace_id)

    def create_invitation(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        invited_email: str,
    ) -> WorkspaceInvitationCreationResult:
        access = self.get_owner_access(workspace_id=workspace_id, current_user=current_user)
        if access.workspace.type == WorkspaceType.PERSONAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Personal workspaces cannot have invitations.",
            )

        normalized_email = invited_email.strip().lower()
        existing_user = self._users.get_by_email(normalized_email)
        if existing_user is not None:
            existing_membership = self._members.get_for_user(
                workspace_id=workspace_id,
                user_id=existing_user.id,
            )
            if existing_membership is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="That user is already a member of this workspace.",
                )

        now = utc_now()
        existing_invitation = self._invitations.get_pending_by_workspace_and_email(
            workspace_id=workspace_id,
            invited_email=normalized_email,
            now=now,
        )
        if existing_invitation is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation for that email already exists.",
            )

        token = generate_urlsafe_token(24)
        invitation = self._invitations.create(
            workspace_id=workspace_id,
            invited_email=normalized_email,
            invited_by_user_id=current_user.id,
            token_hash=hash_workspace_invitation_token(token, self._settings),
            expires_at=now + timedelta(seconds=self._settings.workspace_invitation_ttl_seconds),
        )
        self._session.commit()
        return WorkspaceInvitationCreationResult(invitation=invitation, token=token)

    def list_invitations(
        self, *, workspace_id: UUID, current_user: User
    ) -> list[WorkspaceInvitation]:
        self.get_owner_access(workspace_id=workspace_id, current_user=current_user)
        invitations = self._invitations.list_by_workspace(workspace_id=workspace_id)
        did_change = False
        now = utc_now()
        for invitation in invitations:
            did_change = self._mark_expired_if_needed(invitation, now=now) or did_change
        if did_change:
            self._session.commit()
        return invitations

    def revoke_invitation(
        self,
        *,
        workspace_id: UUID,
        invitation_id: UUID,
        current_user: User,
    ) -> WorkspaceInvitation:
        self.get_owner_access(workspace_id=workspace_id, current_user=current_user)
        invitation = self._invitations.get_by_id(
            workspace_id=workspace_id, invitation_id=invitation_id
        )
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found.",
            )

        now = utc_now()
        if self._mark_expired_if_needed(invitation, now=now):
            self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has expired.",
            )

        if invitation.status == WorkspaceInvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Accepted invitations cannot be revoked.",
            )
        if invitation.status == WorkspaceInvitationStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has already been revoked.",
            )
        if invitation.status == WorkspaceInvitationStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has expired.",
            )

        revoked_invitation = self._invitations.mark_revoked(invitation, revoked_at=now)
        self._session.commit()
        return revoked_invitation

    def accept_invitation(self, *, token: str, current_user: User) -> WorkspaceAccess:
        invitation = self._invitations.get_by_token_hash(
            token_hash=hash_workspace_invitation_token(token, self._settings)
        )
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token is invalid.",
            )

        if invitation.invited_email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation is not valid for this user.",
            )

        now = utc_now()
        if self._mark_expired_if_needed(invitation, now=now):
            self._session.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has expired.",
            )

        if invitation.status == WorkspaceInvitationStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has been revoked.",
            )
        if invitation.status == WorkspaceInvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has already been accepted.",
            )
        if invitation.status == WorkspaceInvitationStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has expired.",
            )

        existing_membership = self._members.get_for_user(
            workspace_id=invitation.workspace_id,
            user_id=current_user.id,
        )
        if existing_membership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this workspace.",
            )

        membership = self._members.create(
            workspace_id=invitation.workspace_id,
            user_id=current_user.id,
            role=WorkspaceMemberRole.MEMBER,
        )
        self._invitations.mark_accepted(
            invitation,
            accepted_by_user_id=current_user.id,
            accepted_at=now,
        )
        self._session.commit()
        return self.get_workspace_access(
            workspace_id=invitation.workspace_id,
            current_user=current_user,
            membership=membership,
        )

    @staticmethod
    def _normalize_workspace_name(name: str) -> str:
        normalized_name = name.strip()
        if normalized_name == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Workspace name must not be empty.",
            )
        return normalized_name

    def _mark_expired_if_needed(self, invitation: WorkspaceInvitation, *, now: datetime) -> bool:
        expires_at = self._coerce_utc_datetime(invitation.expires_at)
        current_time = self._coerce_utc_datetime(now)
        if invitation.status == WorkspaceInvitationStatus.PENDING and expires_at <= current_time:
            self._invitations.mark_expired(invitation)
            return True
        return False

    @staticmethod
    def _coerce_utc_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
