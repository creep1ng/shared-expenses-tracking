from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NetBalanceUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class NetBalanceEntry(BaseModel):
    debtor_id: UUID
    creditor_id: UUID
    amount_minor: int
    currency: str
    debtor: NetBalanceUserSummary | None = None
    creditor: NetBalanceUserSummary | None = None


class NetBalanceResponse(BaseModel):
    balances: list[NetBalanceEntry]
