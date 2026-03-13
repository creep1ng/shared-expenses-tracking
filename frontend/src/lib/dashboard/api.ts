import { requestJson } from "@/lib/api/client";
import type { DashboardKpiQuery, DashboardKpiResponse } from "@/lib/dashboard/types";

export function getWorkspaceDashboardKpis(
  workspaceId: string,
  query: DashboardKpiQuery,
): Promise<DashboardKpiResponse> {
  const searchParams = new URLSearchParams({
    start_date: query.startDate,
    end_date: query.endDate,
  });

  return requestJson<DashboardKpiResponse>(
    `/workspaces/${workspaceId}/dashboard/kpis?${searchParams.toString()}`,
    {
      method: "GET",
    },
  );
}
