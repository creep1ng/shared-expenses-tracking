from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator


class DashboardKpiKind(str, Enum):
    TOTAL_BALANCE = "total_balance"
    TOTAL_INCOME = "total_income"
    TOTAL_EXPENSES = "total_expenses"
    NET_CASH_FLOW = "net_cash_flow"


class DashboardKpiStatus(str, Enum):
    AVAILABLE = "available"
    NO_DATA = "no_data"
    MIXED_CURRENCY = "mixed_currency"


class DashboardKpiQueryParams(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self) -> "DashboardKpiQueryParams":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date.")
        return self

    def to_date_range(self) -> "DashboardDateRange":
        start_at = datetime.combine(self.start_date, time.min, tzinfo=UTC)
        end_at_exclusive = datetime.combine(self.end_date + timedelta(days=1), time.min, tzinfo=UTC)
        return DashboardDateRange(
            start_date=self.start_date,
            end_date=self.end_date,
            start_at=start_at,
            end_at_exclusive=end_at_exclusive,
        )


class DashboardDateRange(BaseModel):
    start_date: date
    end_date: date
    start_at: datetime
    end_at_exclusive: datetime

    @field_validator("start_at", "end_at_exclusive", mode="before")
    @classmethod
    def coerce_datetime_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_serializer("start_at", "end_at_exclusive")
    def serialize_datetime(self, value: datetime) -> str:
        normalized_value = value.astimezone(UTC)
        return normalized_value.isoformat().replace("+00:00", "Z")


class DashboardAvailableKpi(BaseModel):
    kind: DashboardKpiKind
    status: Literal[DashboardKpiStatus.AVAILABLE]
    amount_minor: int
    currency: str


class DashboardNoDataKpi(BaseModel):
    kind: DashboardKpiKind
    status: Literal[DashboardKpiStatus.NO_DATA]


class DashboardMixedCurrencyKpi(BaseModel):
    kind: DashboardKpiKind
    status: Literal[DashboardKpiStatus.MIXED_CURRENCY]


DashboardKpiValue = Annotated[
    DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi,
    Field(discriminator="status"),
]


class DashboardKpiResponse(BaseModel):
    date_range: DashboardDateRange
    total_balance: DashboardKpiValue
    total_income: DashboardKpiValue
    total_expenses: DashboardKpiValue
    net_cash_flow: DashboardKpiValue
