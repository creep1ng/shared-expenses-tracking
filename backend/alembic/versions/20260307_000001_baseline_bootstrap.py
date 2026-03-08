"""baseline bootstrap

Revision ID: 20260307_000001
Revises:
Create Date: 2026-03-07 00:00:01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260307_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "migration_heartbeat",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.bulk_insert(
        sa.table(
            "migration_heartbeat",
            sa.column("name", sa.String(length=50)),
        ),
        [{"name": "baseline"}],
    )


def downgrade() -> None:
    op.drop_table("migration_heartbeat")
