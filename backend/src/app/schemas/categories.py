from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import CategoryType


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: CategoryType
    icon: str = Field(min_length=1, max_length=64)
    color: str = Field(min_length=1, max_length=32)


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: CategoryType | None = None
    icon: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, min_length=1, max_length=32)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    type: CategoryType
    icon: str
    color: str
    archived_at: datetime | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
