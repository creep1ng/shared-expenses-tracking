from __future__ import annotations

from datetime import date

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.workspaces import get_workspace_service
from app.db.session import get_db_session
from app.schemas.dashboard import DashboardKpiQueryParams
from app.services.dashboard import DashboardService
from app.services.workspaces import WorkspaceService


def get_dashboard_kpi_query_params(
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> DashboardKpiQueryParams:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date.",
        )
    return DashboardKpiQueryParams(start_date=start_date, end_date=end_date)


def get_dashboard_service(
    session: Session = Depends(get_db_session),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> DashboardService:
    return DashboardService(session=session, workspace_service=workspace_service)
