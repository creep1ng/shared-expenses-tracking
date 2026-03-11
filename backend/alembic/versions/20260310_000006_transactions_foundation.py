"""transactions foundation

Revision ID: 20260310_000006
Revises: 20260308_000005
Create Date: 2026-03-10 00:00:06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260310_000006"
down_revision = "20260308_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "income",
                "expense",
                "transfer",
                name="transaction_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("source_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("paid_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("split_config", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount_minor > 0", name=op.f("ck_transactions_amount_minor_positive")),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_transactions_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_source_account_id_accounts"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["destination_account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_destination_account_id_accounts"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paid_by_user_id"],
            ["users.id"],
            name=op.f("fk_transactions_paid_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(
        op.f("ix_transactions_workspace_id"),
        "transactions",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_source_account_id"),
        "transactions",
        ["source_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_destination_account_id"),
        "transactions",
        ["destination_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_category_id"),
        "transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_paid_by_user_id"),
        "transactions",
        ["paid_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_occurred_at"),
        "transactions",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_workspace_id_occurred_at",
        "transactions",
        ["workspace_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_workspace_id_occurred_at", table_name="transactions")
    op.drop_index(op.f("ix_transactions_occurred_at"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_paid_by_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_destination_account_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_source_account_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_workspace_id"), table_name="transactions")
    op.drop_table("transactions")
