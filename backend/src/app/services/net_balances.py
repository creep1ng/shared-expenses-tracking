from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import User
from app.repositories.auth import UserRepository
from app.repositories.net_balances import NetBalanceRepository
from app.repositories.workspaces import WorkspaceMemberRepository
from app.services.workspaces import WorkspaceService


@dataclass(frozen=True)
class NetBalanceEntry:
    debtor_id: UUID
    creditor_id: UUID
    amount_minor: int
    currency: str
    debtor_email: str
    creditor_email: str


class NetBalanceService:
    def __init__(
        self,
        session: Session,
        workspace_service: WorkspaceService,
    ) -> None:
        self._session = session
        self._workspace_service = workspace_service
        self._net_balances = NetBalanceRepository(session)
        self._members = WorkspaceMemberRepository(session)
        self._users = UserRepository(session)

    def get_net_balances(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        filter_user_id: UUID | None = None,
    ) -> list[NetBalanceEntry]:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )

        pairwise = self._net_balances.compute_pairwise_net(workspace_id=workspace_id)

        entries: list[NetBalanceEntry] = []
        for (debtor_id, creditor_id, currency), amount in pairwise.items():
            if filter_user_id is not None:
                if debtor_id != filter_user_id and creditor_id != filter_user_id:
                    continue

            debtor = self._users.get_by_id(debtor_id)
            creditor = self._users.get_by_id(creditor_id)
            if debtor is None or creditor is None:
                continue

            entries.append(
                NetBalanceEntry(
                    debtor_id=debtor_id,
                    creditor_id=creditor_id,
                    amount_minor=amount,
                    currency=currency,
                    debtor_email=debtor.email,
                    creditor_email=creditor.email,
                )
            )

        return entries
