import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DashboardKpiOverview } from "@/components/dashboard/dashboard-kpi-overview";

const getWorkspaceDashboardKpisMock = vi.fn();

vi.mock("@/lib/dashboard/api", () => ({
  getWorkspaceDashboardKpis: (...args: unknown[]) => getWorkspaceDashboardKpisMock(...args),
}));

describe("DashboardKpiOverview", () => {
  const today = new Date("2026-03-12T12:00:00Z");

  beforeEach(() => {
    getWorkspaceDashboardKpisMock.mockReset();
  });

  it("renders KPI cards from API data using the default 30-day preset", async () => {
    getWorkspaceDashboardKpisMock.mockResolvedValue({
      date_range: {
        start_date: "2026-02-11",
        end_date: "2026-03-12",
        start_at: "2026-02-11T00:00:00Z",
        end_at_exclusive: "2026-03-13T00:00:00Z",
      },
      total_balance: {
        kind: "total_balance",
        status: "available",
        amount_minor: 155000,
        currency: "ARS",
      },
      total_income: {
        kind: "total_income",
        status: "available",
        amount_minor: 20000,
        currency: "ARS",
      },
      total_expenses: {
        kind: "total_expenses",
        status: "available",
        amount_minor: 5000,
        currency: "ARS",
      },
      net_cash_flow: {
        kind: "net_cash_flow",
        status: "available",
        amount_minor: 15000,
        currency: "ARS",
      },
    });

    render(<DashboardKpiOverview today={today} workspaceId="workspace-1" />);

    await waitFor(() => {
      expect(getWorkspaceDashboardKpisMock).toHaveBeenCalledWith("workspace-1", {
        startDate: "2026-02-11",
        endDate: "2026-03-12",
      });
    });

    expect(await screen.findByText("1550,00 ARS")).toBeInTheDocument();
    expect(screen.getByText("200,00 ARS")).toBeInTheDocument();
    expect(screen.getByText("50,00 ARS")).toBeInTheDocument();
    expect(screen.getByText("150,00 ARS")).toBeInTheDocument();
    expect(screen.getByText(/del 11 feb al 12 mar/i)).toBeInTheDocument();
  });

  it("reloads KPI data when the selected preset changes", async () => {
    const user = userEvent.setup();

    getWorkspaceDashboardKpisMock
      .mockResolvedValueOnce({
        date_range: {
          start_date: "2026-02-11",
          end_date: "2026-03-12",
          start_at: "2026-02-11T00:00:00Z",
          end_at_exclusive: "2026-03-13T00:00:00Z",
        },
        total_balance: {
          kind: "total_balance",
          status: "available",
          amount_minor: 100000,
          currency: "ARS",
        },
        total_income: {
          kind: "total_income",
          status: "available",
          amount_minor: 10000,
          currency: "ARS",
        },
        total_expenses: {
          kind: "total_expenses",
          status: "available",
          amount_minor: 3000,
          currency: "ARS",
        },
        net_cash_flow: {
          kind: "net_cash_flow",
          status: "available",
          amount_minor: 7000,
          currency: "ARS",
        },
      })
      .mockResolvedValueOnce({
        date_range: {
          start_date: "2026-03-06",
          end_date: "2026-03-12",
          start_at: "2026-03-06T00:00:00Z",
          end_at_exclusive: "2026-03-13T00:00:00Z",
        },
        total_balance: {
          kind: "total_balance",
          status: "available",
          amount_minor: 99000,
          currency: "ARS",
        },
        total_income: {
          kind: "total_income",
          status: "available",
          amount_minor: 5000,
          currency: "ARS",
        },
        total_expenses: {
          kind: "total_expenses",
          status: "available",
          amount_minor: 4000,
          currency: "ARS",
        },
        net_cash_flow: {
          kind: "net_cash_flow",
          status: "available",
          amount_minor: 1000,
          currency: "ARS",
        },
      });

    render(<DashboardKpiOverview today={today} workspaceId="workspace-1" />);

    expect(await screen.findByText("1000,00 ARS")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /ultimos 7 dias/i }));

    await waitFor(() => {
      expect(getWorkspaceDashboardKpisMock).toHaveBeenNthCalledWith(2, "workspace-1", {
        startDate: "2026-03-06",
        endDate: "2026-03-12",
      });
    });

    expect(await screen.findByText("990,00 ARS")).toBeInTheDocument();
    expect(screen.getByText(/del 6 mar al 12 mar/i)).toBeInTheDocument();
  });

  it("renders no-data and mixed-currency states gracefully", async () => {
    getWorkspaceDashboardKpisMock.mockResolvedValue({
      date_range: {
        start_date: "2026-02-11",
        end_date: "2026-03-12",
        start_at: "2026-02-11T00:00:00Z",
        end_at_exclusive: "2026-03-13T00:00:00Z",
      },
      total_balance: {
        kind: "total_balance",
        status: "mixed_currency",
      },
      total_income: {
        kind: "total_income",
        status: "no_data",
      },
      total_expenses: {
        kind: "total_expenses",
        status: "no_data",
      },
      net_cash_flow: {
        kind: "net_cash_flow",
        status: "mixed_currency",
      },
    });

    render(<DashboardKpiOverview today={today} workspaceId="workspace-1" />);

    expect(await screen.findAllByText("No disponible")).toHaveLength(2);
    expect(screen.getAllByText("Sin datos")).toHaveLength(2);
    expect(
      screen.getAllByText(/este calculo no se muestra cuando hay cuentas activas en distintas monedas/i),
    ).toHaveLength(2);
    expect(
      screen.getAllByText(/no hay datos disponibles para este indicador en el periodo seleccionado/i),
    ).toHaveLength(2);
  });

  it("reloads KPI data when transaction changes trigger a refresh", async () => {
    getWorkspaceDashboardKpisMock.mockResolvedValue({
      date_range: {
        start_date: "2026-02-11",
        end_date: "2026-03-12",
        start_at: "2026-02-11T00:00:00Z",
        end_at_exclusive: "2026-03-13T00:00:00Z",
      },
      total_balance: {
        kind: "total_balance",
        status: "available",
        amount_minor: 120000,
        currency: "ARS",
      },
      total_income: {
        kind: "total_income",
        status: "available",
        amount_minor: 10000,
        currency: "ARS",
      },
      total_expenses: {
        kind: "total_expenses",
        status: "available",
        amount_minor: 3000,
        currency: "ARS",
      },
      net_cash_flow: {
        kind: "net_cash_flow",
        status: "available",
        amount_minor: 7000,
        currency: "ARS",
      },
    });

    const { rerender } = render(<DashboardKpiOverview refreshNonce={0} today={today} workspaceId="workspace-1" />);

    await waitFor(() => {
      expect(getWorkspaceDashboardKpisMock).toHaveBeenCalledTimes(1);
    });

    rerender(<DashboardKpiOverview refreshNonce={1} today={today} workspaceId="workspace-1" />);
  
    await waitFor(() => {
      expect(getWorkspaceDashboardKpisMock).toHaveBeenCalledTimes(2);
    });
  });
});
