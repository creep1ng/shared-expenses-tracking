from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import AccountType


class AccountCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    currency: str = Field(min_length=3, max_length=3)
    initial_balance_minor: int
    description: str | None = Field(default=None, max_length=1000)


class AccountUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: AccountType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    initial_balance_minor: int | None = None
    description: str | None = Field(default=None, max_length=1000)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    owner_user_id: UUID | None
    name: str
    type: AccountType
    currency: str
    initial_balance_minor: int
    current_balance_minor: int
    description: str | None
    archived_at: datetime | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class AccountListResponse(BaseModel):
    accounts: list[AccountResponse]
