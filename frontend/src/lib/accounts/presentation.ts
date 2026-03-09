import type { AccountType } from "@/lib/accounts/types";
import type { AccountFormValues } from "@/lib/accounts/schemas";

export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  cash: "Efectivo",
  bank_account: "Cuenta bancaria",
  savings_account: "Cuenta de ahorro",
  credit_card: "Tarjeta de credito",
};

export const ACCOUNT_TYPE_OPTIONS: Array<{ value: AccountType; label: string }> = [
  { value: "cash", label: ACCOUNT_TYPE_LABELS.cash },
  { value: "bank_account", label: ACCOUNT_TYPE_LABELS.bank_account },
  { value: "savings_account", label: ACCOUNT_TYPE_LABELS.savings_account },
  { value: "credit_card", label: ACCOUNT_TYPE_LABELS.credit_card },
];

export function parseMoneyInputToMinorUnits(value: string): number {
  const normalizedValue = value.trim().replace(",", ".");
  const isNegative = normalizedValue.startsWith("-");
  const unsignedValue = isNegative ? normalizedValue.slice(1) : normalizedValue;
  const [wholePart, decimalPart = ""] = unsignedValue.split(".");
  const paddedDecimals = `${decimalPart}00`.slice(0, 2);
  const minorUnits = Number.parseInt(wholePart, 10) * 100 + Number.parseInt(paddedDecimals, 10);

  return isNegative ? -minorUnits : minorUnits;
}

export function formatMinorUnitsAsCurrency(value: number, currency: string): string {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency,
  }).format(value / 100);
}

export function formatMinorUnitsForInput(value: number): string {
  const sign = value < 0 ? "-" : "";
  const absoluteValue = Math.abs(value);
  const wholePart = Math.trunc(absoluteValue / 100);
  const decimalPart = `${absoluteValue % 100}`.padStart(2, "0");

  return `${sign}${wholePart}.${decimalPart}`;
}

export function buildAccountPayload(values: AccountFormValues) {
  const trimmedDescription = values.description?.trim() ?? "";

  return {
    name: values.name.trim(),
    type: values.type,
    currency: values.currency.trim().toUpperCase(),
    initial_balance_minor: parseMoneyInputToMinorUnits(values.initialBalance),
    description: trimmedDescription.length > 0 ? trimmedDescription : null,
  };
}
