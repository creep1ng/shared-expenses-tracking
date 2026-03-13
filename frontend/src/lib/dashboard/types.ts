export type DashboardKpiKind = "total_balance" | "total_income" | "total_expenses" | "net_cash_flow";

export type DashboardKpiStatus = "available" | "no_data" | "mixed_currency";

export type DashboardDateRange = {
  start_date: string;
  end_date: string;
  start_at: string;
  end_at_exclusive: string;
};

export type DashboardAvailableKpi = {
  kind: DashboardKpiKind;
  status: "available";
  amount_minor: number;
  currency: string;
};

export type DashboardNoDataKpi = {
  kind: DashboardKpiKind;
  status: "no_data";
};

export type DashboardMixedCurrencyKpi = {
  kind: DashboardKpiKind;
  status: "mixed_currency";
};

export type DashboardKpiValue = DashboardAvailableKpi | DashboardNoDataKpi | DashboardMixedCurrencyKpi;

export type DashboardKpiResponse = {
  date_range: DashboardDateRange;
  total_balance: DashboardKpiValue;
  total_income: DashboardKpiValue;
  total_expenses: DashboardKpiValue;
  net_cash_flow: DashboardKpiValue;
};

export type DashboardKpiQuery = {
  startDate: string;
  endDate: string;
};
