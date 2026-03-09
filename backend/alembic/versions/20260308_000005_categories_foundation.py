"""categories foundation

Revision ID: 20260308_000005
Revises: 20260308_000004
Create Date: 2026-03-08 00:00:05
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260308_000005"
down_revision = "20260308_000004"
branch_labels = None
depends_on = None


DEFAULT_CATEGORIES: tuple[dict[str, str], ...] = (
    {"name": "Comida", "type": "expense", "icon": "utensils-crossed", "color": "#D97706"},
    {"name": "Compras", "type": "expense", "icon": "shopping-bag", "color": "#DB2777"},
    {"name": "Hogar", "type": "expense", "icon": "house", "color": "#2563EB"},
    {"name": "Transporte", "type": "expense", "icon": "car-front", "color": "#0891B2"},
    {"name": "Salud", "type": "expense", "icon": "heart-pulse", "color": "#DC2626"},
    {"name": "Entretenimiento", "type": "expense", "icon": "film", "color": "#7C3AED"},
    {"name": "Servicios", "type": "expense", "icon": "receipt-text", "color": "#4B5563"},
    {"name": "Gastos financieros", "type": "expense", "icon": "landmark", "color": "#0F766E"},
    {"name": "Salario", "type": "income", "icon": "briefcase-business", "color": "#15803D"},
    {"name": "Freelance", "type": "income", "icon": "laptop-minimal", "color": "#16A34A"},
    {"name": "Inversiones", "type": "income", "icon": "chart-column", "color": "#65A30D"},
    {"name": "Otros ingresos", "type": "income", "icon": "wallet", "color": "#059669"},
)


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "type",
            sa.Enum("income", "expense", name="category_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("icon", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=False),
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
            name=op.f("fk_categories_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index(
        op.f("ix_categories_workspace_id"),
        "categories",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(op.f("ix_categories_archived_at"), "categories", ["archived_at"], unique=False)
    op.create_index(
        "uq_categories_workspace_id_type_active_name",
        "categories",
        ["workspace_id", "type", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
        sqlite_where=sa.text("archived_at IS NULL"),
    )

    connection = op.get_bind()
    now = datetime.now(UTC)
    workspace_ids = [
        row[0] for row in connection.execute(sa.text("SELECT id FROM workspaces")).all()
    ]
    for category in DEFAULT_CATEGORIES:
        for workspace_id in workspace_ids:
            exists = connection.execute(
                sa.text(
                    """
                    SELECT 1
                    FROM categories
                    WHERE workspace_id = :workspace_id
                      AND type = :type
                      AND lower(name) = lower(:name)
                    """
                ),
                {"workspace_id": workspace_id, **category},
            ).first()
            if exists is not None:
                continue

            connection.execute(
                sa.text(
                    """
                    INSERT INTO categories (
                        id,
                        workspace_id,
                        name,
                        type,
                        icon,
                        color,
                        archived_at,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :workspace_id,
                        :name,
                        :type,
                        :icon,
                        :color,
                        NULL,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": uuid4(),
                    "workspace_id": workspace_id,
                    "created_at": now,
                    "updated_at": now,
                    **category,
                },
            )


def downgrade() -> None:
    op.drop_index("uq_categories_workspace_id_type_active_name", table_name="categories")
    op.drop_index(op.f("ix_categories_archived_at"), table_name="categories")
    op.drop_index(op.f("ix_categories_workspace_id"), table_name="categories")
    op.drop_table("categories")
