"""accounts foundation

Revision ID: 20260308_000004
Revises: 20260308_000003
Create Date: 2026-03-08 00:00:04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260308_000004"
down_revision = "20260308_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "cash",
                "bank_account",
                "savings_account",
                "credit_card",
                name="account_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("initial_balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("current_balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_accounts_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_index(op.f("ix_accounts_workspace_id"), "accounts", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_accounts_archived_at"), "accounts", ["archived_at"], unique=False)
    op.create_index(
        "uq_accounts_workspace_id_active_name",
        "accounts",
        ["workspace_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
        sqlite_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_accounts_workspace_id_active_name", table_name="accounts")
    op.drop_index(op.f("ix_accounts_archived_at"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_workspace_id"), table_name="accounts")
    op.drop_table("accounts")
