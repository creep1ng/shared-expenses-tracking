"""Add scheduled payments table

Revision ID: 20260408_000010
Revises: 20260408_000009
Create Date: 2026-04-08 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260408_000010"
down_revision = "20260408_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduled_payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("next_due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scheduled_payments_category_id"),
        "scheduled_payments",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_payments_last_executed_at"),
        "scheduled_payments",
        ["last_executed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_payments_next_due_date"),
        "scheduled_payments",
        ["next_due_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_payments_workspace_id"),
        "scheduled_payments",
        ["workspace_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "scheduled_payments", "categories", ["category_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_foreign_key(
        None, "scheduled_payments", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint(None, "scheduled_payments", type_="foreignkey")
    op.drop_constraint(None, "scheduled_payments", type_="foreignkey")
    op.drop_index(op.f("ix_scheduled_payments_workspace_id"), table_name="scheduled_payments")
    op.drop_index(op.f("ix_scheduled_payments_next_due_date"), table_name="scheduled_payments")
    op.drop_index(op.f("ix_scheduled_payments_last_executed_at"), table_name="scheduled_payments")
    op.drop_index(op.f("ix_scheduled_payments_category_id"), table_name="scheduled_payments")
    op.drop_table("scheduled_payments")
