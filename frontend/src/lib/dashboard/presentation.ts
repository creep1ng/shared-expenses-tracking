import type { DashboardDateRange, DashboardKpiQuery } from "@/lib/dashboard/types";

export type DashboardPresetKey = "last_7_days" | "last_30_days" | "last_90_days";

type DashboardPreset = {
  key: DashboardPresetKey;
  label: string;
  days: number;
};

export const DASHBOARD_PRESETS: DashboardPreset[] = [
  { key: "last_7_days", label: "Ultimos 7 dias", days: 7 },
  { key: "last_30_days", label: "Ultimos 30 dias", days: 30 },
  { key: "last_90_days", label: "Ultimos 90 dias", days: 90 },
];

export const DEFAULT_DASHBOARD_PRESET_KEY: DashboardPresetKey = "last_30_days";

function toUtcDateOnly(value: Date): Date {
  return new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()));
}

function formatDateParam(value: Date): string {
  const year = value.getUTCFullYear();
  const month = `${value.getUTCMonth() + 1}`.padStart(2, "0");
  const day = `${value.getUTCDate()}`.padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function parseDateParam(value: string): Date {
  return new Date(`${value}T00:00:00Z`);
}

export function getDashboardPresetRange(presetKey: DashboardPresetKey, now: Date = new Date()): DashboardKpiQuery {
  const preset = DASHBOARD_PRESETS.find((candidate) => candidate.key === presetKey) ?? DASHBOARD_PRESETS[1];
  const endDate = toUtcDateOnly(now);
  const startDate = new Date(endDate);

  startDate.setUTCDate(startDate.getUTCDate() - (preset.days - 1));

  return {
    startDate: formatDateParam(startDate),
    endDate: formatDateParam(endDate),
  };
}

export function formatDashboardRangeLabel(dateRange: Pick<DashboardDateRange, "start_date" | "end_date">): string {
  const formatter = new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });

  return `Del ${formatter.format(parseDateParam(dateRange.start_date))} al ${formatter.format(parseDateParam(dateRange.end_date))}`;
}
