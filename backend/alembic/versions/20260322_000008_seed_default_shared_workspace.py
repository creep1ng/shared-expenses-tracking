"""seed default shared workspace for existing users

Revision ID: 20260322_000008
Revises: 20260311_000007
Create Date: 2026-03-22 00:00:08
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260322_000008"
down_revision = "20260311_000007"
branch_labels = None
depends_on = None

DEFAULT_CATEGORIES = [
    ("Comida", "expense", "utensils-crossed", "#D97706"),
    ("Compras", "expense", "shopping-bag", "#DB2777"),
    ("Hogar", "expense", "house", "#2563EB"),
    ("Transporte", "expense", "car-front", "#0891B2"),
    ("Salud", "expense", "heart-pulse", "#DC2626"),
    ("Entretenimiento", "expense", "film", "#7C3AED"),
    ("Servicios", "expense", "receipt-text", "#4B5563"),
    ("Gastos financieros", "expense", "landmark", "#0F766E"),
    ("Salario", "income", "briefcase-business", "#15803D"),
    ("Freelance", "income", "laptop-minimal", "#16A34A"),
    ("Inversiones", "income", "chart-column", "#65A30D"),
    ("Otros ingresos", "income", "wallet", "#059669"),
]


def upgrade() -> None:
    """Create a default shared workspace for each user who doesn't have one."""
    bind = op.get_bind()

    users_result = sa.text("SELECT id FROM users").execute(bind)
    user_ids = [row[0] for row in users_result]

    for user_id in user_ids:
        existing = (
            sa.text(
                "SELECT 1 FROM workspace_members wm "
                "JOIN workspaces w ON w.id = wm.workspace_id "
                "WHERE wm.user_id = :user_id AND w.type = 'shared' "
                "LIMIT 1"
            )
            .execute(bind, {"user_id": user_id})
            .first()
        )

        if existing is not None:
            continue

        workspace_id = uuid.uuid4()
        now = datetime.now(UTC)

        sa.text(
            "INSERT INTO workspaces (id, name, type, created_by_user_id, created_at, updated_at) "
            "VALUES (:id, :name, :type, :created_by, :now, :now)"
        ).execute(
            bind,
            {
                "id": workspace_id,
                "name": "Gastos compartidos",
                "type": "shared",
                "created_by": user_id,
                "now": now,
            },
        )

        member_id = uuid.uuid4()
        sa.text(
            "INSERT INTO workspace_members "
            "(id, workspace_id, user_id, role, created_at, updated_at) "
            "VALUES (:id, :workspace_id, :user_id, :role, :now, :now)"
        ).execute(
            bind,
            {
                "id": member_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": "owner",
                "now": now,
            },
        )

        _seed_default_categories(bind, workspace_id, now)


def _seed_default_categories(
    bind: sa.engine.Connection,
    workspace_id: uuid.UUID,
    now: datetime,
) -> None:
    """Seed default categories matching DEFAULT_WORKSPACE_CATEGORY_SEEDS."""
    for name, cat_type, icon, color in DEFAULT_CATEGORIES:
        category_id = uuid.uuid4()
        sa.text(
            "INSERT INTO categories "
            "(id, workspace_id, name, type, icon, color, created_at, updated_at) "
            "VALUES (:id, :workspace_id, :name, :type, :icon, :color, :now, :now)"
        ).execute(
            bind,
            {
                "id": category_id,
                "workspace_id": workspace_id,
                "name": name,
                "type": cat_type,
                "icon": icon,
                "color": color,
                "now": now,
            },
        )


def downgrade() -> None:
    """Remove seeded shared workspaces (only those named 'Gastos compartidos')."""
    bind = op.get_bind()

    workspaces = sa.text("SELECT id FROM workspaces WHERE name = 'Gastos compartidos'").execute(
        bind
    )

    for (workspace_id,) in workspaces:
        sa.text("DELETE FROM categories WHERE workspace_id = :wid").execute(
            bind, {"wid": workspace_id}
        )
        sa.text("DELETE FROM workspace_members WHERE workspace_id = :wid").execute(
            bind, {"wid": workspace_id}
        )
        sa.text("DELETE FROM workspaces WHERE id = :wid").execute(bind, {"wid": workspace_id})
