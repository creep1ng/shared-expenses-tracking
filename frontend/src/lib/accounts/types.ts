export type AccountType = "cash" | "bank_account" | "savings_account" | "credit_card";

export type Account = {
  id: string;
  workspace_id: string;
  name: string;
  type: AccountType;
  currency: string;
  initial_balance_minor: number;
  current_balance_minor: number;
  description: string | null;
  archived_at: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type AccountListResponse = {
  accounts: Account[];
};

export type AccountCreatePayload = {
  name: string;
  type: AccountType;
  currency: string;
  initial_balance_minor: number;
  description?: string | null;
};

export type AccountUpdatePayload = Partial<AccountCreatePayload>;
