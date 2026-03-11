export type TransactionType = "income" | "expense" | "transfer";

export type TransactionAccountSummary = {
  id: string;
  workspace_id: string;
  name: string;
  type: "cash" | "bank_account" | "savings_account" | "credit_card";
  currency: string;
  archived_at: string | null;
  is_archived: boolean;
};

export type TransactionCategorySummary = {
  id: string;
  workspace_id: string;
  name: string;
  type: "income" | "expense";
  archived_at: string | null;
  is_archived: boolean;
};

export type TransactionUserSummary = {
  id: string;
  email: string;
};

export type Transaction = {
  id: string;
  workspace_id: string;
  type: TransactionType;
  source_account_id: string | null;
  destination_account_id: string | null;
  category_id: string | null;
  paid_by_user_id: string | null;
  amount_minor: number;
  currency: string;
  description: string | null;
  occurred_at: string;
  split_config: Record<string, unknown> | null;
  source_account: TransactionAccountSummary | null;
  destination_account: TransactionAccountSummary | null;
  category: TransactionCategorySummary | null;
  paid_by_user: TransactionUserSummary | null;
  created_at: string;
  updated_at: string;
};

export type TransactionListResponse = {
  transactions: Transaction[];
};

export type TransactionCreatePayload = {
  type: TransactionType;
  source_account_id: string | null;
  destination_account_id: string | null;
  category_id: string | null;
  paid_by_user_id: string | null;
  amount_minor: number;
  currency: string;
  description?: string | null;
  occurred_at: string;
  split_config?: Record<string, unknown> | null;
};

export type TransactionUpdatePayload = Partial<TransactionCreatePayload>;
