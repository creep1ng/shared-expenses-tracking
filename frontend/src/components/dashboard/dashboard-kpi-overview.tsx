"use client";

import React from "react";
import { useEffect, useMemo, useState } from "react";

import { formatMinorUnitsAsCurrency } from "@/lib/accounts/presentation";
import { getErrorMessage } from "@/lib/auth/errors";
import { getWorkspaceDashboardKpis } from "@/lib/dashboard/api";
import {
  DASHBOARD_PRESETS,
  DEFAULT_DASHBOARD_PRESET_KEY,
  formatDashboardRangeLabel,
  getDashboardPresetRange,
  type DashboardPresetKey,
} from "@/lib/dashboard/presentation";
import type { DashboardKpiResponse, DashboardKpiValue } from "@/lib/dashboard/types";

type DashboardKpiOverviewProps = {
  workspaceId: string;
  refreshNonce?: number;
  today?: Date;
};

type KpiCardDescriptor = {
  key: keyof Pick<DashboardKpiResponse, "total_balance" | "total_income" | "total_expenses" | "net_cash_flow">;
  label: string;
};

type KpiCardContent = {
  detail: string;
  tone: "default" | "positive" | "negative" | "muted";
  value: string;
};

const KPI_CARD_DESCRIPTORS: KpiCardDescriptor[] = [
  { key: "total_balance", label: "Balance total" },
  { key: "total_income", label: "Ingresos del periodo" },
  { key: "total_expenses", label: "Gastos del periodo" },
  { key: "net_cash_flow", label: "Flujo neto" },
];

function getKpiCardContent(kpi: DashboardKpiValue): KpiCardContent {
  if (kpi.status === "available") {
    const tone =
      kpi.kind === "total_income"
        ? "positive"
        : kpi.kind === "total_expenses"
          ? "negative"
          : kpi.kind === "net_cash_flow"
            ? kpi.amount_minor >= 0
              ? "positive"
              : "negative"
            : "default";

    return {
      value: formatMinorUnitsAsCurrency(kpi.amount_minor, kpi.currency),
      detail: `Moneda ${kpi.currency}`,
      tone,
    };
  }

  if (kpi.status === "mixed_currency") {
    return {
      value: "No disponible",
      detail: "Este calculo no se muestra cuando hay cuentas activas en distintas monedas.",
      tone: "muted",
    };
  }

  return {
    value: "Sin datos",
    detail: "No hay datos disponibles para este indicador en el periodo seleccionado.",
    tone: "muted",
  };
}

export function DashboardKpiOverview({ workspaceId, refreshNonce = 0, today }: DashboardKpiOverviewProps) {
  const [selectedPresetKey, setSelectedPresetKey] = useState<DashboardPresetKey>(DEFAULT_DASHBOARD_PRESET_KEY);
  const [kpis, setKpis] = useState<DashboardKpiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const selectedRange = useMemo(() => getDashboardPresetRange(selectedPresetKey, today ?? new Date()), [selectedPresetKey, today]);

  useEffect(() => {
    let isActive = true;

    const loadKpis = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      setKpis(null);

      try {
        const response = await getWorkspaceDashboardKpis(workspaceId, selectedRange);

        if (!isActive) {
          return;
        }

        setKpis(response);
      } catch (error) {
        if (!isActive) {
          return;
        }

        setErrorMessage(getErrorMessage(error));
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void loadKpis();

    return () => {
      isActive = false;
    };
  }, [refreshNonce, selectedRange, workspaceId]);

  const rangeLabel = kpis ? formatDashboardRangeLabel(kpis.date_range) : null;

  return (
    <section className="workspace-panel dashboard-kpi-panel" aria-labelledby="dashboard-kpi-title">
      <div className="dashboard-kpi-header">
        <div className="workspace-form-header">
          <span className="dashboard-eyebrow">Panorama</span>
          <h2 className="workspace-section-title" id="dashboard-kpi-title">
            Indicadores clave
          </h2>
          <p className="workspace-section-copy dashboard-kpi-copy">
            {rangeLabel ?? "Consulta el balance, los ingresos, los gastos y el flujo neto del periodo."}
          </p>
        </div>

        <div aria-label="Seleccionar periodo del tablero" className="dashboard-preset-group" role="group">
          {DASHBOARD_PRESETS.map((preset) => (
            <button
              aria-pressed={preset.key === selectedPresetKey}
              className={`dashboard-preset-button ${preset.key === selectedPresetKey ? "dashboard-preset-button-active" : ""}`}
              key={preset.key}
              onClick={() => {
                setSelectedPresetKey(preset.key);
              }}
              type="button"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {errorMessage ? (
        <div className="auth-feedback auth-feedback-error" role="alert">
          {errorMessage}
        </div>
      ) : null}

      <div className="dashboard-kpi-grid">
        {KPI_CARD_DESCRIPTORS.map((descriptor) => {
          const kpi = kpis?.[descriptor.key];
          const content = kpi ? getKpiCardContent(kpi) : null;

          return (
            <article
              className={`dashboard-kpi-card ${kpi ? `dashboard-kpi-card-${kpi.status}` : "dashboard-kpi-card-loading"}`}
              data-state={kpi?.status ?? "loading"}
              key={descriptor.key}
            >
              <span className="dashboard-kpi-label">{descriptor.label}</span>
              <strong
                className={`dashboard-kpi-value ${content ? `dashboard-kpi-value-${content.tone}` : "dashboard-kpi-value-muted"}`}
              >
                {content ? content.value : isLoading ? "Cargando..." : "-"}
              </strong>
              <p className="dashboard-kpi-meta">
                {content ? content.detail : isLoading ? "Actualizando indicadores del periodo seleccionado." : ""}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
