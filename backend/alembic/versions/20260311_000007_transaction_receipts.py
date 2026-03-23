"""transaction receipts

Revision ID: 20260311_000007
Revises: 20260310_000006
Create Date: 2026-03-11 00:00:07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260311_000007"
down_revision = "20260310_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("receipt_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "receipt_url")
