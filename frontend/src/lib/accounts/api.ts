import { requestJson } from "@/lib/api/client";
import type {
  Account,
  AccountCreatePayload,
  AccountListResponse,
  AccountUpdatePayload,
} from "@/lib/accounts/types";

type ListAccountsOptions = {
  includeArchived?: boolean;
};

export function listAccounts(
  workspaceId: string,
  options: ListAccountsOptions = {},
): Promise<AccountListResponse> {
  const query = options.includeArchived ? "?include_archived=true" : "";

  return requestJson<AccountListResponse>(`/workspaces/${workspaceId}/accounts${query}`, {
    method: "GET",
  });
}

export function createAccount(workspaceId: string, payload: AccountCreatePayload): Promise<Account> {
  return requestJson<Account>(`/workspaces/${workspaceId}/accounts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAccount(
  workspaceId: string,
  accountId: string,
  payload: AccountUpdatePayload,
): Promise<Account> {
  return requestJson<Account>(`/workspaces/${workspaceId}/accounts/${accountId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveAccount(workspaceId: string, accountId: string): Promise<Account> {
  return requestJson<Account>(`/workspaces/${workspaceId}/accounts/${accountId}/archive`, {
    method: "POST",
  });
}
