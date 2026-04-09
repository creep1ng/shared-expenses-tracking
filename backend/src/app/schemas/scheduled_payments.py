from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ScheduledPaymentFrequency


class ScheduledPaymentCreateRequest(BaseModel):
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category_id: UUID | None = None
    description: str | None = Field(default=None, max_length=1000)
    frequency: ScheduledPaymentFrequency
    next_due_date: datetime


class ScheduledPaymentUpdateRequest(BaseModel):
    amount_minor: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category_id: UUID | None = None
    description: str | None = Field(default=None, max_length=1000)
    frequency: ScheduledPaymentFrequency | None = None
    next_due_date: datetime | None = None
    is_active: bool | None = None


class ScheduledPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    amount_minor: int
    currency: str
    category_id: UUID | None
    description: str | None
    frequency: ScheduledPaymentFrequency
    next_due_date: datetime
    last_executed_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScheduledPaymentListResponse(BaseModel):
    scheduled_payments: list[ScheduledPaymentResponse]
