from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class WorkspaceType(str, Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class WorkspaceMemberRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"


class WorkspaceInvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AccountType(str, Enum):
    CASH = "cash"
    BANK_ACCOUNT = "bank_account"
    SAVINGS_ACCOUNT = "savings_account"
    CREDIT_CARD = "credit_card"


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=True, server_default="true"
    )

    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_workspaces: Mapped[list[Workspace]] = relationship(
        back_populates="creator",
        foreign_keys="Workspace.created_by_user_id",
    )
    workspace_memberships: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sent_workspace_invitations: Mapped[list[WorkspaceInvitation]] = relationship(
        back_populates="invited_by_user",
        foreign_keys="WorkspaceInvitation.invited_by_user_id",
    )
    accepted_workspace_invitations: Mapped[list[WorkspaceInvitation]] = relationship(
        back_populates="accepted_by_user",
        foreign_keys="WorkspaceInvitation.accepted_by_user_id",
    )


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[WorkspaceType] = mapped_column(
        SAEnum(
            WorkspaceType,
            name="workspace_type",
            native_enum=False,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    creator: Mapped[User] = relationship(
        back_populates="created_workspaces",
        foreign_keys=[created_by_user_id],
    )
    members: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list[WorkspaceInvitation]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    accounts: Mapped[list[Account]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list[Category]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class WorkspaceMember(TimestampMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "user_id", name="uq_workspace_members_workspace_id_user_id"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[WorkspaceMemberRole] = mapped_column(
        SAEnum(
            WorkspaceMemberRole,
            name="workspace_member_role",
            native_enum=False,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="workspace_memberships")


class WorkspaceInvitation(TimestampMixin, Base):
    __tablename__ = "workspace_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_workspace_invitations_token_hash"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    invited_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[WorkspaceInvitationStatus] = mapped_column(
        SAEnum(
            WorkspaceInvitationStatus,
            name="workspace_invitation_status",
            native_enum=False,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=WorkspaceInvitationStatus.PENDING,
        server_default=WorkspaceInvitationStatus.PENDING.value,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="invitations")
    invited_by_user: Mapped[User] = relationship(
        back_populates="sent_workspace_invitations",
        foreign_keys=[invited_by_user_id],
    )
    accepted_by_user: Mapped[User | None] = relationship(
        back_populates="accepted_workspace_invitations",
        foreign_keys=[accepted_by_user_id],
    )


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        SAEnum(
            AccountType,
            name="account_type",
            native_enum=False,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    initial_balance_minor: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    current_balance_minor: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        Index(
            "uq_accounts_workspace_id_active_name",
            "workspace_id",
            func.lower(name),
            unique=True,
            postgresql_where=archived_at.is_(None),
            sqlite_where=archived_at.is_(None),
        ),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="accounts")

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[CategoryType] = mapped_column(
        SAEnum(
            CategoryType,
            name="category_type",
            native_enum=False,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )
    icon: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(32), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        Index(
            "uq_categories_workspace_id_type_active_name",
            "workspace_id",
            "type",
            func.lower(name),
            unique=True,
            postgresql_where=archived_at.is_(None),
            sqlite_where=archived_at.is_(None),
        ),
    )

    workspace: Mapped[Workspace] = relationship(back_populates="categories")

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
