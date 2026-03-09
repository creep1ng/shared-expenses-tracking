from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceInvitationStatus,
    WorkspaceMember,
    WorkspaceMemberRole,
    WorkspaceType,
)


class WorkspaceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self, *, name: str, workspace_type: WorkspaceType, created_by_user_id: UUID
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            type=workspace_type,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(workspace)
        self._session.flush()
        self._session.refresh(workspace)
        return workspace

    def update_name(self, workspace: Workspace, *, name: str) -> Workspace:
        workspace.name = name
        self._session.add(workspace)
        self._session.flush()
        self._session.refresh(workspace)
        return workspace


class WorkspaceMemberRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceMemberRole
    ) -> WorkspaceMember:
        membership = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        self._session.add(membership)
        self._session.flush()
        self._session.refresh(membership)
        return membership

    def get_for_user(self, *, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        statement = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .options(
                joinedload(WorkspaceMember.workspace).selectinload(Workspace.members),
                joinedload(WorkspaceMember.workspace).selectinload(Workspace.invitations),
                joinedload(WorkspaceMember.user),
            )
        )
        return self._session.scalar(statement)

    def list_for_user(self, *, user_id: UUID) -> list[WorkspaceMember]:
        statement = (
            select(WorkspaceMember)
            .where(WorkspaceMember.user_id == user_id)
            .options(
                joinedload(WorkspaceMember.workspace).selectinload(Workspace.members),
                joinedload(WorkspaceMember.user),
            )
            .order_by(WorkspaceMember.created_at.asc())
        )
        return list(self._session.scalars(statement).all())

    def list_by_workspace(self, *, workspace_id: UUID) -> list[WorkspaceMember]:
        statement = (
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .options(joinedload(WorkspaceMember.user))
            .order_by(WorkspaceMember.created_at.asc())
        )
        return list(self._session.scalars(statement).all())


class WorkspaceInvitationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        workspace_id: UUID,
        invited_email: str,
        invited_by_user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> WorkspaceInvitation:
        invitation = WorkspaceInvitation(
            workspace_id=workspace_id,
            invited_email=invited_email,
            invited_by_user_id=invited_by_user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(invitation)
        self._session.flush()
        self._session.refresh(invitation)
        return invitation

    def get_by_id(self, *, workspace_id: UUID, invitation_id: UUID) -> WorkspaceInvitation | None:
        statement = (
            select(WorkspaceInvitation)
            .where(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.id == invitation_id,
            )
            .options(joinedload(WorkspaceInvitation.workspace))
        )
        return self._session.scalar(statement)

    def get_by_token_hash(self, *, token_hash: str) -> WorkspaceInvitation | None:
        statement = (
            select(WorkspaceInvitation)
            .where(WorkspaceInvitation.token_hash == token_hash)
            .options(joinedload(WorkspaceInvitation.workspace))
        )
        return self._session.scalar(statement)

    def get_pending_by_workspace_and_email(
        self,
        *,
        workspace_id: UUID,
        invited_email: str,
        now: datetime,
    ) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.invited_email == invited_email,
            WorkspaceInvitation.status == WorkspaceInvitationStatus.PENDING,
            WorkspaceInvitation.expires_at > now,
        )
        return self._session.scalar(statement)

    def list_by_workspace(self, *, workspace_id: UUID) -> list[WorkspaceInvitation]:
        statement = (
            select(WorkspaceInvitation)
            .where(WorkspaceInvitation.workspace_id == workspace_id)
            .order_by(WorkspaceInvitation.created_at.desc())
        )
        return list(self._session.scalars(statement).all())

    def mark_accepted(
        self,
        invitation: WorkspaceInvitation,
        *,
        accepted_by_user_id: UUID,
        accepted_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.status = WorkspaceInvitationStatus.ACCEPTED
        invitation.accepted_by_user_id = accepted_by_user_id
        invitation.accepted_at = accepted_at
        self._session.add(invitation)
        self._session.flush()
        self._session.refresh(invitation)
        return invitation

    def mark_revoked(
        self,
        invitation: WorkspaceInvitation,
        *,
        revoked_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.status = WorkspaceInvitationStatus.REVOKED
        invitation.revoked_at = revoked_at
        self._session.add(invitation)
        self._session.flush()
        self._session.refresh(invitation)
        return invitation

    def mark_expired(self, invitation: WorkspaceInvitation) -> WorkspaceInvitation:
        invitation.status = WorkspaceInvitationStatus.EXPIRED
        self._session.add(invitation)
        self._session.flush()
        self._session.refresh(invitation)
        return invitation
