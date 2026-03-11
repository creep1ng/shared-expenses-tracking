from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.db.models import AccountType, CategoryType, TransactionType


def _validate_occurred_at_not_future(v: datetime) -> datetime:
    if v.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware.")
    now = datetime.now(UTC)
    if v > now:
        raise ValueError("occurred_at cannot be in the future.")
    return v


class TransactionCreateRequest(BaseModel):
    type: TransactionType
    source_account_id: UUID | None = None
    destination_account_id: UUID | None = None
    category_id: UUID | None = None
    paid_by_user_id: UUID | None = None
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=1000)
    occurred_at: datetime
    split_config: dict[str, Any] | None = None

    _occurred_at_not_future = field_validator("occurred_at", mode="after")(
        _validate_occurred_at_not_future
    )


class TransactionUpdateRequest(BaseModel):
    type: TransactionType | None = None
    source_account_id: UUID | None = None
    destination_account_id: UUID | None = None
    category_id: UUID | None = None
    paid_by_user_id: UUID | None = None
    amount_minor: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=1000)
    occurred_at: datetime | None = None
    split_config: dict[str, Any] | None = None

    _occurred_at_not_future = field_validator("occurred_at", mode="after")(
        lambda v: _validate_occurred_at_not_future(v) if v is not None else v
    )


class TransactionAccountSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    type: AccountType
    currency: str
    archived_at: datetime | None
    is_archived: bool


class TransactionCategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    type: CategoryType
    archived_at: datetime | None
    is_archived: bool


class TransactionUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    type: TransactionType
    source_account_id: UUID | None
    destination_account_id: UUID | None
    category_id: UUID | None
    paid_by_user_id: UUID | None
    amount_minor: int
    currency: str
    description: str | None
    occurred_at: datetime
    split_config: dict[str, Any] | None
    receipt_url: str | None
    source_account: TransactionAccountSummary | None
    destination_account: TransactionAccountSummary | None
    category: TransactionCategorySummary | None
    paid_by_user: TransactionUserSummary | None
    created_at: datetime
    updated_at: datetime

    @field_validator("occurred_at", "created_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_serializer("occurred_at", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        normalized_value = value.astimezone(UTC)
        return normalized_value.isoformat().replace("+00:00", "Z")


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]


class TransactionReceiptUploadResponse(BaseModel):
    receipt_url: str | None
