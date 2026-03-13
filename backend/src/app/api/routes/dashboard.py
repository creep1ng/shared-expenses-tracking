from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.dashboard import get_dashboard_kpi_query_params, get_dashboard_service
from app.db.models import User
from app.schemas.dashboard import DashboardKpiQueryParams, DashboardKpiResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/workspaces/{workspace_id}/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=DashboardKpiResponse)
def get_dashboard_kpis(
    workspace_id: UUID,
    query: DashboardKpiQueryParams = Depends(get_dashboard_kpi_query_params),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardKpiResponse:
    return dashboard_service.get_kpis(
        workspace_id=workspace_id,
        current_user=current_user,
        query=query,
    )
