import { requestJson, requestVoid } from "@/lib/api/client";
import type {
  Transaction,
  TransactionCreatePayload,
  TransactionListResponse,
  TransactionUpdatePayload,
} from "@/lib/transactions/types";

export function listTransactions(workspaceId: string): Promise<TransactionListResponse> {
  return requestJson<TransactionListResponse>(`/workspaces/${workspaceId}/transactions`, {
    method: "GET",
  });
}

export function getTransaction(workspaceId: string, transactionId: string): Promise<Transaction> {
  return requestJson<Transaction>(`/workspaces/${workspaceId}/transactions/${transactionId}`, {
    method: "GET",
  });
}

export function createTransaction(
  workspaceId: string,
  payload: TransactionCreatePayload,
): Promise<Transaction> {
  return requestJson<Transaction>(`/workspaces/${workspaceId}/transactions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTransaction(
  workspaceId: string,
  transactionId: string,
  payload: TransactionUpdatePayload,
): Promise<Transaction> {
  return requestJson<Transaction>(`/workspaces/${workspaceId}/transactions/${transactionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTransaction(workspaceId: string, transactionId: string): Promise<void> {
  return requestVoid(`/workspaces/${workspaceId}/transactions/${transactionId}`, {
    method: "DELETE",
  });
}
