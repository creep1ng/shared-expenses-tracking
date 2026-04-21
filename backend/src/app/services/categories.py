from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Category, CategoryType, User
from app.repositories.categories import CategoryRepository
from app.services.workspaces import WorkspaceService


class CategoryService:
    def __init__(self, session: Session, workspace_service: WorkspaceService) -> None:
        self._session = session
        self._workspace_service = workspace_service
        self._categories = CategoryRepository(session)

    DUPLICATE_ACTIVE_CATEGORY_DETAIL = (
        "An active category with that type and name already exists in this workspace."
    )

    def create_category(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        name: str,
        category_type: CategoryType,
        icon: str,
        color: str,
        parent_id: UUID | None = None,
    ) -> Category:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        normalized_name = self._normalize_name(name)
        normalized_icon = self._normalize_icon(icon)
        normalized_color = self._normalize_color(color)
        self._ensure_active_name_available(
            workspace_id=workspace_id,
            name=normalized_name,
            category_type=category_type,
        )

        if parent_id is not None:
            parent_category = self._get_category_or_404(
                workspace_id=workspace_id, category_id=parent_id
            )
            if parent_category.type != category_type:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Parent category must be of the same type.",
                )
            if parent_category.archived_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot use archived category as parent.",
                )

        try:
            category = self._categories.create(
                workspace_id=workspace_id,
                name=normalized_name,
                category_type=category_type,
                icon=normalized_icon,
                color=normalized_color,
                parent_id=parent_id,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if self._is_duplicate_name_error(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=self.DUPLICATE_ACTIVE_CATEGORY_DETAIL,
                ) from exc
            raise

        return category

    def list_categories(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        include_archived: bool,
    ) -> list[Category]:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        return self._categories.list_by_workspace(
            workspace_id=workspace_id,
            include_archived=include_archived,
        )

    def update_category(
        self,
        *,
        workspace_id: UUID,
        category_id: UUID,
        current_user: User,
        updates: dict[str, Any],
    ) -> Category:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        category = self._get_category_or_404(workspace_id=workspace_id, category_id=category_id)
        if category.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Archived categories cannot be updated.",
            )

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided.",
            )

        updated_name = (
            self._normalize_name(str(updates["name"])) if "name" in updates else category.name
        )
        updated_type = CategoryType(updates["type"]) if "type" in updates else category.type
        updated_icon = (
            self._normalize_icon(str(updates["icon"])) if "icon" in updates else category.icon
        )
        updated_color = (
            self._normalize_color(str(updates["color"])) if "color" in updates else category.color
        )
        updated_parent_id = updates.get("parent_id", category.parent_id)

        if "parent_id" in updates and updated_parent_id is not None:
            parent_category = self._get_category_or_404(
                workspace_id=workspace_id, category_id=updated_parent_id
            )
            if parent_category.type != updated_type:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Parent category must be of the same type.",
                )
            if parent_category.archived_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot use archived category as parent.",
                )
            # Validar que no se crea un bucle recursivo
            if self._would_create_cycle(category.id, updated_parent_id):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot set parent: this would create a cycle in category hierarchy.",
                )

        self._ensure_active_name_available(
            workspace_id=workspace_id,
            name=updated_name,
            category_type=updated_type,
            exclude_category_id=category.id,
        )

        try:
            updated_category = self._categories.update(
                category,
                name=updated_name,
                category_type=updated_type,
                icon=updated_icon,
                color=updated_color,
                parent_id=updated_parent_id,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if self._is_duplicate_name_error(exc):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=self.DUPLICATE_ACTIVE_CATEGORY_DETAIL,
                ) from exc
            raise

        return updated_category

    def archive_category(
        self,
        *,
        workspace_id: UUID,
        category_id: UUID,
        current_user: User,
    ) -> Category:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )
        category = self._get_category_or_404(workspace_id=workspace_id, category_id=category_id)
        if category.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category has already been archived.",
            )

        archived_category = self._categories.archive(category, archived_at=utc_now())
        self._session.commit()
        return archived_category

    def _get_category_or_404(self, *, workspace_id: UUID, category_id: UUID) -> Category:
        category = self._categories.get_by_id(workspace_id=workspace_id, category_id=category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        return category

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized_name = name.strip()
        if normalized_name == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category name must not be empty.",
            )
        return normalized_name

    @staticmethod
    def _normalize_icon(icon: str) -> str:
        normalized_icon = icon.strip()
        if normalized_icon == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category icon must not be empty.",
            )
        return normalized_icon

    @staticmethod
    def _normalize_color(color: str) -> str:
        normalized_color = color.strip()
        if normalized_color == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category color must not be empty.",
            )
        return normalized_color

    def _ensure_active_name_available(
        self,
        *,
        workspace_id: UUID,
        name: str,
        category_type: CategoryType,
        exclude_category_id: UUID | None = None,
    ) -> None:
        duplicate_category = self._categories.get_active_by_name(
            workspace_id=workspace_id,
            name=name,
            category_type=category_type,
            exclude_category_id=exclude_category_id,
        )
        if duplicate_category is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=self.DUPLICATE_ACTIVE_CATEGORY_DETAIL,
            )

    def _would_create_cycle(self, category_id: UUID, new_parent_id: UUID) -> bool:
        """Check if setting new_parent_id as parent of category_id would create a cycle."""
        visited: set[UUID] = set()
        current_id: UUID | None = new_parent_id

        while current_id is not None:
            if current_id == category_id:
                return True
            if current_id in visited:
                return True  # Existing cycle somewhere up, just prevent
            visited.add(current_id)

            current = self._categories.get_by_id_raw(current_id)
            current_id = current.parent_id if current else None

        return False

    @staticmethod
    def _is_duplicate_name_error(exc: IntegrityError) -> bool:
        return "uq_categories_workspace_id_type_active_name" in str(exc.orig)
