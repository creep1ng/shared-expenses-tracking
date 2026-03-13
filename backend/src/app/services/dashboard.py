from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import TransactionType, User
from app.repositories.dashboard import (
    AccountCurrencyBalanceTotal,
    AnalyticsCurrencyTotal,
    DashboardRepository,
)
from app.schemas.dashboard import (
    DashboardAvailableKpi,
    DashboardKpiKind,
    DashboardKpiQueryParams,
    DashboardKpiResponse,
    DashboardKpiStatus,
    DashboardMixedCurrencyKpi,
    DashboardNoDataKpi,
)
from app.services.workspaces import WorkspaceService


@dataclass(frozen=True)
class AnalyticsSummary:
    currency: str
    income_minor: int
    expense_minor: int


class DashboardService:
    def __init__(self, session: Session, workspace_service: WorkspaceService) -> None:
        self._workspace_service = workspace_service
        self._dashboard = DashboardRepository(session)

    def get_kpis(
        self,
        *,
        workspace_id: UUID,
        current_user: User,
        query: DashboardKpiQueryParams,
    ) -> DashboardKpiResponse:
        self._workspace_service.get_workspace_access(
            workspace_id=workspace_id,
            current_user=current_user,
        )

        date_range = query.to_date_range()
        balance_totals = self._dashboard.list_active_account_balance_totals(
            workspace_id=workspace_id
        )
        analytics_totals = self._dashboard.list_period_analytics_totals(
            workspace_id=workspace_id,
            start_at=date_range.start_at,
            end_at_exclusive=date_range.end_at_exclusive,
        )

        return DashboardKpiResponse(
            date_range=date_range,
            total_balance=self._build_balance_kpi(balance_totals=balance_totals),
            total_income=self._build_income_kpi(analytics_totals=analytics_totals),
            total_expenses=self._build_expenses_kpi(analytics_totals=analytics_totals),
            net_cash_flow=self._build_net_cash_flow_kpi(analytics_totals=analytics_totals),
        )

    @staticmethod
    def _build_balance_kpi(
        *, balance_totals: list[AccountCurrencyBalanceTotal]
    ) -> DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi:
        if not balance_totals:
            return DashboardNoDataKpi(
                kind=DashboardKpiKind.TOTAL_BALANCE,
                status=DashboardKpiStatus.NO_DATA,
            )

        if len(balance_totals) > 1:
            return DashboardMixedCurrencyKpi(
                kind=DashboardKpiKind.TOTAL_BALANCE,
                status=DashboardKpiStatus.MIXED_CURRENCY,
            )

        balance_total = balance_totals[0]
        return DashboardAvailableKpi(
            kind=DashboardKpiKind.TOTAL_BALANCE,
            status=DashboardKpiStatus.AVAILABLE,
            amount_minor=balance_total.amount_minor,
            currency=balance_total.currency,
        )

    def _build_income_kpi(
        self,
        *,
        analytics_totals: list[AnalyticsCurrencyTotal],
    ) -> DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi:
        analytics_summary = self._summarize_analytics(analytics_totals=analytics_totals)
        if analytics_summary is None:
            return DashboardNoDataKpi(
                kind=DashboardKpiKind.TOTAL_INCOME,
                status=DashboardKpiStatus.NO_DATA,
            )

        if not isinstance(analytics_summary, AnalyticsSummary):
            return DashboardMixedCurrencyKpi(
                kind=DashboardKpiKind.TOTAL_INCOME,
                status=DashboardKpiStatus.MIXED_CURRENCY,
            )

        return DashboardAvailableKpi(
            kind=DashboardKpiKind.TOTAL_INCOME,
            status=DashboardKpiStatus.AVAILABLE,
            amount_minor=analytics_summary.income_minor,
            currency=analytics_summary.currency,
        )

    def _build_expenses_kpi(
        self,
        *,
        analytics_totals: list[AnalyticsCurrencyTotal],
    ) -> DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi:
        analytics_summary = self._summarize_analytics(analytics_totals=analytics_totals)
        if analytics_summary is None:
            return DashboardNoDataKpi(
                kind=DashboardKpiKind.TOTAL_EXPENSES,
                status=DashboardKpiStatus.NO_DATA,
            )

        if not isinstance(analytics_summary, AnalyticsSummary):
            return DashboardMixedCurrencyKpi(
                kind=DashboardKpiKind.TOTAL_EXPENSES,
                status=DashboardKpiStatus.MIXED_CURRENCY,
            )

        return DashboardAvailableKpi(
            kind=DashboardKpiKind.TOTAL_EXPENSES,
            status=DashboardKpiStatus.AVAILABLE,
            amount_minor=analytics_summary.expense_minor,
            currency=analytics_summary.currency,
        )

    def _build_net_cash_flow_kpi(
        self,
        *,
        analytics_totals: list[AnalyticsCurrencyTotal],
    ) -> DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi:
        analytics_summary = self._summarize_analytics(analytics_totals=analytics_totals)
        if analytics_summary is None:
            return DashboardNoDataKpi(
                kind=DashboardKpiKind.NET_CASH_FLOW,
                status=DashboardKpiStatus.NO_DATA,
            )

        if not isinstance(analytics_summary, AnalyticsSummary):
            return DashboardMixedCurrencyKpi(
                kind=DashboardKpiKind.NET_CASH_FLOW,
                status=DashboardKpiStatus.MIXED_CURRENCY,
            )

        return DashboardAvailableKpi(
            kind=DashboardKpiKind.NET_CASH_FLOW,
            status=DashboardKpiStatus.AVAILABLE,
            amount_minor=analytics_summary.income_minor - analytics_summary.expense_minor,
            currency=analytics_summary.currency,
        )

    @staticmethod
    def _summarize_analytics(
        *, analytics_totals: list[AnalyticsCurrencyTotal]
    ) -> AnalyticsSummary | Literal[DashboardKpiStatus.MIXED_CURRENCY] | None:
        if not analytics_totals:
            return None

        currencies = {item.currency for item in analytics_totals}
        if len(currencies) > 1:
            return DashboardKpiStatus.MIXED_CURRENCY

        currency = next(iter(currencies))
        income_minor = 0
        expense_minor = 0
        for item in analytics_totals:
            if item.transaction_type is TransactionType.INCOME:
                income_minor += item.amount_minor
            if item.transaction_type is TransactionType.EXPENSE:
                expense_minor += item.amount_minor

        return AnalyticsSummary(
            currency=currency,
            income_minor=income_minor,
            expense_minor=expense_minor,
        )
