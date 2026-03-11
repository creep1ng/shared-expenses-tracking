import type { Account } from "@/lib/accounts/types";
import {
  formatMinorUnitsAsCurrency,
  formatMinorUnitsForInput,
  parseMoneyInputToMinorUnits,
} from "@/lib/accounts/presentation";
import type { Category } from "@/lib/categories/types";
import type { TransactionFormValues } from "@/lib/transactions/schemas";
import type { Transaction, TransactionCreatePayload, TransactionType } from "@/lib/transactions/types";
import { formatDateTime } from "@/lib/workspaces/presentation";

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  income: "Ingreso",
  expense: "Gasto",
  transfer: "Transferencia",
};

export const TRANSACTION_TYPE_OPTIONS: Array<{ value: TransactionType; label: string }> = [
  { value: "expense", label: TRANSACTION_TYPE_LABELS.expense },
  { value: "income", label: TRANSACTION_TYPE_LABELS.income },
  { value: "transfer", label: TRANSACTION_TYPE_LABELS.transfer },
];

export function getCurrentDateTimeInputValue(): string {
  return formatDateForInput(new Date());
}

export function getMaxDateTimeInputValue(): string {
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return formatDateForInput(today);
}

export function formatIsoDateTimeForInput(value: string): string {
  return formatDateForInput(new Date(value));
}

function formatDateForInput(value: Date): string {
  if (Number.isNaN(value.getTime())) {
    return "";
  }

  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  const hours = `${value.getHours()}`.padStart(2, "0");
  const minutes = `${value.getMinutes()}`.padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function convertLocalDateTimeInputToIso(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    throw new Error("Indica una fecha y hora validas.");
  }

  return date.toISOString();
}

export function getSelectableTransactionAccounts(accounts: Account[]): Account[] {
  return [...accounts]
    .filter((account) => !account.is_archived)
    .sort((left, right) => left.name.localeCompare(right.name, "es"));
}

export function getSelectableTransactionCategories(
  categories: Category[],
  transactionType: TransactionType,
): Category[] {
  if (transactionType === "transfer") {
    return [];
  }

  return [...categories]
    .filter((category) => !category.is_archived && category.type === transactionType)
    .sort((left, right) => left.name.localeCompare(right.name, "es"));
}

export function resolveTransactionCurrency(
  values: Pick<TransactionFormValues, "type" | "sourceAccountId" | "destinationAccountId">,
  accounts: Account[],
): string | null {
  const accountsById = new Map(accounts.map((account) => [account.id, account]));
  const sourceAccount = values.sourceAccountId ? accountsById.get(values.sourceAccountId) : undefined;
  const destinationAccount = values.destinationAccountId
    ? accountsById.get(values.destinationAccountId)
    : undefined;

  if (values.type === "income") {
    return destinationAccount?.currency ?? null;
  }

  if (values.type === "expense") {
    return sourceAccount?.currency ?? null;
  }

  if (!sourceAccount || !destinationAccount || sourceAccount.currency !== destinationAccount.currency) {
    return null;
  }

  return sourceAccount.currency;
}

export function buildTransactionPayload(
  values: TransactionFormValues,
  accounts: Account[],
): TransactionCreatePayload {
  const sourceAccountId = values.sourceAccountId?.trim() || null;
  const destinationAccountId = values.destinationAccountId?.trim() || null;
  const categoryId = values.categoryId?.trim() || null;
  const currency = resolveTransactionCurrency(values, accounts);

  if (!currency) {
    throw new Error(
      values.type === "transfer"
        ? "La transferencia requiere cuentas activas con la misma moneda."
        : "Selecciona una cuenta activa para definir la moneda del movimiento.",
    );
  }

  const description = values.description?.trim() ?? "";

  return {
    type: values.type,
    source_account_id: values.type === "income" ? null : sourceAccountId,
    destination_account_id: values.type === "expense" ? null : destinationAccountId,
    category_id: values.type === "transfer" ? null : categoryId,
    paid_by_user_id: null,
    amount_minor: parseMoneyInputToMinorUnits(values.amount),
    currency,
    description: description.length > 0 ? description : null,
    occurred_at: convertLocalDateTimeInputToIso(values.occurredAt),
    split_config: null,
  };
}

export function toTransactionFormDefaults(transaction: Transaction): TransactionFormValues {
  return {
    type: transaction.type,
    sourceAccountId: transaction.source_account_id ?? "",
    destinationAccountId: transaction.destination_account_id ?? "",
    categoryId: transaction.category_id ?? "",
    amount: formatMinorUnitsForInput(transaction.amount_minor),
    occurredAt: formatIsoDateTimeForInput(transaction.occurred_at),
    description: transaction.description ?? "",
  };
}

export function sortTransactionsChronologically(transactions: Transaction[]): Transaction[] {
  return [...transactions].sort((left, right) => {
    const occurredAtDifference = new Date(right.occurred_at).getTime() - new Date(left.occurred_at).getTime();

    if (occurredAtDifference !== 0) {
      return occurredAtDifference;
    }

    return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
  });
}

export function formatTransactionAmount(transaction: Transaction): string {
  const amount = formatMinorUnitsAsCurrency(transaction.amount_minor, transaction.currency);

  if (transaction.type === "income") {
    return `+ ${amount}`;
  }

  if (transaction.type === "expense") {
    return `- ${amount}`;
  }

  return amount;
}

export function getTransactionRouteLabel(transaction: Transaction): string {
  if (transaction.type === "income") {
    return `En ${transaction.destination_account?.name ?? "cuenta desconocida"}`;
  }

  if (transaction.type === "expense") {
    return `Desde ${transaction.source_account?.name ?? "cuenta desconocida"}`;
  }

  return `${transaction.source_account?.name ?? "Cuenta origen"} -> ${transaction.destination_account?.name ?? "Cuenta destino"}`;
}

export function getTransactionHeadline(transaction: Transaction): string {
  if (transaction.description) {
    return transaction.description;
  }

  if (transaction.type === "transfer") {
    return "Transferencia entre cuentas";
  }

  return transaction.category?.name ?? TRANSACTION_TYPE_LABELS[transaction.type];
}

export function getTransactionMetaLabel(transaction: Transaction): string {
  const dateLabel = formatDateTime(transaction.occurred_at);

  if (transaction.type === "transfer") {
    return `${TRANSACTION_TYPE_LABELS.transfer} · ${dateLabel}`;
  }

  return `${transaction.category?.name ?? "Sin categoria"} · ${dateLabel}`;
}

export function formatTransactionOccurredAt(value: string): string {
  return formatDateTime(value);
}

function getReceiptPathname(receiptUrl: string): string {
  try {
    return new URL(receiptUrl, "http://localhost").pathname.toLowerCase();
  } catch {
    return receiptUrl.toLowerCase();
  }
}

export function getTransactionReceiptKind(receiptUrl: string | null): "image" | "pdf" | "file" | null {
  if (!receiptUrl) {
    return null;
  }

  const normalizedUrl = receiptUrl.trim().toLowerCase();

  if (normalizedUrl.startsWith("data:image/")) {
    return "image";
  }

  if (normalizedUrl.startsWith("data:application/pdf")) {
    return "pdf";
  }

  const pathname = getReceiptPathname(receiptUrl);

  if (/\.(png|jpe?g|gif|webp|bmp|svg|avif)$/i.test(pathname)) {
    return "image";
  }

  if (pathname.endsWith(".pdf")) {
    return "pdf";
  }

  return "file";
}
