from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.categories import get_category_service
from app.db.models import Category, User
from app.schemas.categories import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.services.categories import CategoryService

router = APIRouter(prefix="/workspaces/{workspace_id}/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    workspace_id: UUID,
    payload: CategoryCreateRequest,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    category = category_service.create_category(
        workspace_id=workspace_id,
        current_user=current_user,
        name=payload.name,
        category_type=payload.type,
        icon=payload.icon,
        color=payload.color,
        parent_id=payload.parent_id,
    )
    return _build_category_response(category)


@router.get("", response_model=CategoryListResponse)
def list_categories(
    workspace_id: UUID,
    include_archived: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryListResponse:
    categories = category_service.list_categories(
        workspace_id=workspace_id,
        current_user=current_user,
        include_archived=include_archived,
    )
    return CategoryListResponse(
        categories=[_build_category_response(category) for category in categories]
    )


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    workspace_id: UUID,
    category_id: UUID,
    payload: CategoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    category = category_service.update_category(
        workspace_id=workspace_id,
        category_id=category_id,
        current_user=current_user,
        updates=payload.model_dump(exclude_unset=True),
    )
    return _build_category_response(category)


@router.post("/{category_id}/archive", response_model=CategoryResponse)
def archive_category(
    workspace_id: UUID,
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    category = category_service.archive_category(
        workspace_id=workspace_id,
        category_id=category_id,
        current_user=current_user,
    )
    return _build_category_response(category)


def _build_category_response(category: Category) -> CategoryResponse:
    return CategoryResponse.model_validate(category)
