"""Add category hierarchy and personal accounts

Revision ID: 20260408_000009
Revises: 20260322_000008
Create Date: 2026-04-08 21:54:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260408_000009"
down_revision = "20260322_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add parent_id column to categories table
    op.add_column("categories", sa.Column("parent_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)
    op.create_foreign_key(
        None, "categories", "categories", ["parent_id"], ["id"], ondelete="SET NULL"
    )

    # Add owner_user_id column to accounts table
    op.add_column("accounts", sa.Column("owner_user_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_accounts_owner_user_id"), "accounts", ["owner_user_id"], unique=False)
    op.create_foreign_key(None, "accounts", "users", ["owner_user_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    # Remove owner_user_id from accounts
    op.drop_constraint(None, "accounts", type_="foreignkey")
    op.drop_index(op.f("ix_accounts_owner_user_id"), table_name="accounts")
    op.drop_column("accounts", "owner_user_id")

    # Remove parent_id from categories
    op.drop_constraint(None, "categories", type_="foreignkey")
    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_column("categories", "parent_id")
