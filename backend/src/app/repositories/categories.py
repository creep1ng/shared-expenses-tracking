from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Category, CategoryType


@dataclass(frozen=True)
class DefaultCategorySeed:
    name: str
    category_type: CategoryType
    icon: str
    color: str


DEFAULT_WORKSPACE_CATEGORY_SEEDS: tuple[DefaultCategorySeed, ...] = (
    DefaultCategorySeed(
        name="Comida",
        category_type=CategoryType.EXPENSE,
        icon="utensils-crossed",
        color="#D97706",
    ),
    DefaultCategorySeed(
        name="Compras",
        category_type=CategoryType.EXPENSE,
        icon="shopping-bag",
        color="#DB2777",
    ),
    DefaultCategorySeed(
        name="Hogar",
        category_type=CategoryType.EXPENSE,
        icon="house",
        color="#2563EB",
    ),
    DefaultCategorySeed(
        name="Transporte",
        category_type=CategoryType.EXPENSE,
        icon="car-front",
        color="#0891B2",
    ),
    DefaultCategorySeed(
        name="Salud",
        category_type=CategoryType.EXPENSE,
        icon="heart-pulse",
        color="#DC2626",
    ),
    DefaultCategorySeed(
        name="Entretenimiento",
        category_type=CategoryType.EXPENSE,
        icon="film",
        color="#7C3AED",
    ),
    DefaultCategorySeed(
        name="Servicios",
        category_type=CategoryType.EXPENSE,
        icon="receipt-text",
        color="#4B5563",
    ),
    DefaultCategorySeed(
        name="Gastos financieros",
        category_type=CategoryType.EXPENSE,
        icon="landmark",
        color="#0F766E",
    ),
    DefaultCategorySeed(
        name="Salario",
        category_type=CategoryType.INCOME,
        icon="briefcase-business",
        color="#15803D",
    ),
    DefaultCategorySeed(
        name="Freelance",
        category_type=CategoryType.INCOME,
        icon="laptop-minimal",
        color="#16A34A",
    ),
    DefaultCategorySeed(
        name="Inversiones",
        category_type=CategoryType.INCOME,
        icon="chart-column",
        color="#65A30D",
    ),
    DefaultCategorySeed(
        name="Otros ingresos",
        category_type=CategoryType.INCOME,
        icon="wallet",
        color="#059669",
    ),
)


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        workspace_id: UUID,
        name: str,
        category_type: CategoryType,
        icon: str,
        color: str,
    ) -> Category:
        category = Category(
            workspace_id=workspace_id,
            name=name,
            type=category_type,
            icon=icon,
            color=color,
        )
        self._session.add(category)
        self._session.flush()
        self._session.refresh(category)
        return category

    def list_by_workspace(self, *, workspace_id: UUID, include_archived: bool) -> list[Category]:
        statement = self._base_query().where(Category.workspace_id == workspace_id)
        if not include_archived:
            statement = statement.where(Category.archived_at.is_(None))
        statement = statement.order_by(Category.type.asc(), Category.created_at.asc())
        return list(self._session.scalars(statement).all())

    def get_by_id(self, *, workspace_id: UUID, category_id: UUID) -> Category | None:
        statement = self._base_query().where(
            Category.workspace_id == workspace_id,
            Category.id == category_id,
        )
        return self._session.scalar(statement)

    def get_active_by_name(
        self,
        *,
        workspace_id: UUID,
        name: str,
        category_type: CategoryType,
        exclude_category_id: UUID | None = None,
    ) -> Category | None:
        statement = self._base_query().where(
            Category.workspace_id == workspace_id,
            Category.type == category_type,
            Category.archived_at.is_(None),
            func.lower(Category.name) == name.lower(),
        )
        if exclude_category_id is not None:
            statement = statement.where(Category.id != exclude_category_id)
        return self._session.scalar(statement)

    def update(
        self,
        category: Category,
        *,
        name: str,
        category_type: CategoryType,
        icon: str,
        color: str,
    ) -> Category:
        category.name = name
        category.type = category_type
        category.icon = icon
        category.color = color
        self._session.add(category)
        self._session.flush()
        self._session.refresh(category)
        return category

    def archive(self, category: Category, *, archived_at: datetime) -> Category:
        category.archived_at = archived_at
        self._session.add(category)
        self._session.flush()
        self._session.refresh(category)
        return category

    def ensure_default_categories_for_workspace(self, *, workspace_id: UUID) -> list[Category]:
        """Seed missing defaults for a workspace.

        This is intentionally idempotent so the same method can be reused during
        workspace creation and for backfill workflows on pre-existing workspaces.
        Any existing matching name/type pair, including archived rows, is treated
        as already seeded so the backfill does not recreate intentionally retired
        defaults.
        """
        existing_keys = {
            (category_type, name.lower())
            for category_type, name in self._session.execute(
                select(Category.type, Category.name).where(Category.workspace_id == workspace_id)
            ).all()
        }

        created_categories: list[Category] = []
        for seed in DEFAULT_WORKSPACE_CATEGORY_SEEDS:
            key = (seed.category_type, seed.name.lower())
            if key in existing_keys:
                continue

            category = Category(
                workspace_id=workspace_id,
                name=seed.name,
                type=seed.category_type,
                icon=seed.icon,
                color=seed.color,
            )
            self._session.add(category)
            created_categories.append(category)
            existing_keys.add(key)

        if created_categories:
            self._session.flush()
            for category in created_categories:
                self._session.refresh(category)

        return created_categories

    @staticmethod
    def _base_query() -> Select[tuple[Category]]:
        return select(Category).options(joinedload(Category.workspace))
