"use client";

import React from "react";
import { useEffect, useMemo, useState } from "react";

import {
  DEFAULT_TRANSACTION_FORM_VALUES,
  TransactionForm,
} from "@/components/transactions/transaction-form";
import { getErrorMessage } from "@/lib/auth/errors";
import { listAccounts } from "@/lib/accounts/api";
import type { Account } from "@/lib/accounts/types";
import { listCategories } from "@/lib/categories/api";
import type { Category } from "@/lib/categories/types";
import { listWorkspaceMembers } from "@/lib/workspaces/api";
import type { WorkspaceMember } from "@/lib/workspaces/types";
import {
  createTransaction,
  deleteTransaction,
  getTransaction,
  listTransactions,
  uploadTransactionReceipt,
  updateTransaction,
} from "@/lib/transactions/api";
import {
  formatTransactionAmount,
  formatTransactionOccurredAt,
  getTransactionReceiptKind,
  getSelectableTransactionAccounts,
  getTransactionHeadline,
  getTransactionMetaLabel,
  getTransactionRouteLabel,
  sortTransactionsChronologically,
  toTransactionFormDefaults,
  TRANSACTION_TYPE_LABELS,
} from "@/lib/transactions/presentation";
import type {
  Transaction,
  TransactionAccountSummary,
  TransactionCategorySummary,
  TransactionCreatePayload,
} from "@/lib/transactions/types";

type TransactionsPanelProps = {
  workspaceId: string;
  onTransactionsChanged?: () => void;
};

type Notice = {
  type: "error" | "success";
  message: string;
};

function summaryToAccount(summary: TransactionAccountSummary): Account {
  return {
    id: summary.id,
    workspace_id: summary.workspace_id,
    name: summary.name,
    type: summary.type,
    currency: summary.currency,
    initial_balance_minor: 0,
    current_balance_minor: 0,
    description: null,
    archived_at: summary.archived_at,
    is_archived: summary.is_archived,
    created_at: "",
    updated_at: "",
  };
}

function summaryToCategory(summary: TransactionCategorySummary): Category {
  return {
    id: summary.id,
    workspace_id: summary.workspace_id,
    parent_id: null,
    name: summary.name,
    type: summary.type,
    icon: "",
    color: "#000000",
    archived_at: summary.archived_at,
    is_archived: summary.is_archived,
    created_at: "",
    updated_at: "",
  };
}

function mergeTransactionAccounts(accounts: Account[], transactions: Transaction[]): Account[] {
  const merged = new Map(accounts.map((account) => [account.id, account]));

  for (const transaction of transactions) {
    if (transaction.source_account && !merged.has(transaction.source_account.id)) {
      merged.set(transaction.source_account.id, summaryToAccount(transaction.source_account));
    }
    if (transaction.destination_account && !merged.has(transaction.destination_account.id)) {
      merged.set(transaction.destination_account.id, summaryToAccount(transaction.destination_account));
    }
  }

  return [...merged.values()].sort((left, right) => left.name.localeCompare(right.name, "es"));
}

function mergeTransactionCategories(categories: Category[], transactions: Transaction[]): Category[] {
  const merged = new Map(categories.map((category) => [category.id, category]));

  for (const transaction of transactions) {
    if (transaction.category && !merged.has(transaction.category.id)) {
      merged.set(transaction.category.id, summaryToCategory(transaction.category));
    }
  }

  return [...merged.values()].sort((left, right) => left.name.localeCompare(right.name, "es"));
}

export function TransactionsPanel({ workspaceId, onTransactionsChanged }: TransactionsPanelProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [expandedTransactionId, setExpandedTransactionId] = useState<string | null>(null);
  const [editingTransactionId, setEditingTransactionId] = useState<string | null>(null);
  const [transactionDetails, setTransactionDetails] = useState<Record<string, Transaction>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [loadingTransactionId, setLoadingTransactionId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);

  const loadPanelData = React.useCallback(async () => {
    setIsLoading(true);

    try {
      const [transactionsResponse, accountsResponse, categoriesResponse, membersResponse] = await Promise.all([
        listTransactions(workspaceId),
        listAccounts(workspaceId),
        listCategories(workspaceId),
        listWorkspaceMembers(workspaceId),
      ]);

      const sortedTransactions = sortTransactionsChronologically(transactionsResponse.transactions);

      setTransactions(sortedTransactions);
      setAccounts(getSelectableTransactionAccounts(accountsResponse.accounts));
      setCategories(categoriesResponse.categories.filter((category) => !category.is_archived));
      setMembers(membersResponse.members);
      setTransactionDetails({});
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    setExpandedTransactionId(null);
    setEditingTransactionId(null);
    setNotice(null);

    void loadPanelData();
  }, [loadPanelData]);

  const formAccounts = useMemo(() => mergeTransactionAccounts(accounts, transactions), [accounts, transactions]);
  const formCategories = useMemo(() => mergeTransactionCategories(categories, transactions), [categories, transactions]);

  const ensureTransactionDetail = React.useCallback(
    async (transactionId: string) => {
      const cachedTransaction = transactionDetails[transactionId];

      if (cachedTransaction) {
        return cachedTransaction;
      }

      setLoadingTransactionId(transactionId);

      try {
        const transaction = await getTransaction(workspaceId, transactionId);
        setTransactionDetails((currentDetails) => ({ ...currentDetails, [transactionId]: transaction }));
        return transaction;
      } finally {
        setLoadingTransactionId(null);
      }
    },
    [transactionDetails, workspaceId],
  );

  const syncTransaction = React.useCallback((transaction: Transaction) => {
    setTransactions((currentTransactions) =>
      sortTransactionsChronologically(
        currentTransactions.some((currentTransaction) => currentTransaction.id === transaction.id)
          ? currentTransactions.map((currentTransaction) =>
              currentTransaction.id === transaction.id ? transaction : currentTransaction,
            )
          : [transaction, ...currentTransactions],
      ),
    );
    setTransactionDetails((currentDetails) => ({ ...currentDetails, [transaction.id]: transaction }));
  }, []);

  const handleCreate = async (payload: TransactionCreatePayload, receiptFile?: File | null) => {
    setNotice(null);

    try {
      const transaction = await createTransaction(workspaceId, payload);

      if (receiptFile) {
        try {
          await uploadTransactionReceipt(workspaceId, transaction.id, receiptFile);
        } catch (error) {
          syncTransaction(transaction);
          setNotice({
            type: "error",
            message: `Movimiento registrado, pero no se pudo adjuntar el recibo: ${getErrorMessage(error)}`,
          });
          await loadPanelData();
          onTransactionsChanged?.();
          return true;
        }
      }

      syncTransaction(transaction);
      setNotice({ type: "success", message: "Movimiento registrado correctamente." });
      await loadPanelData();
      onTransactionsChanged?.();
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleOpenDetail = async (transactionId: string) => {
    if (expandedTransactionId === transactionId) {
      setExpandedTransactionId(null);
      return;
    }

    setNotice(null);

    try {
      await ensureTransactionDetail(transactionId);
      setExpandedTransactionId(transactionId);
      setEditingTransactionId(null);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  const handleOpenEdit = async (transactionId: string) => {
    setNotice(null);

    try {
      await ensureTransactionDetail(transactionId);
      setEditingTransactionId((currentId) => (currentId === transactionId ? null : transactionId));
      setExpandedTransactionId(transactionId);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  const handleUpdate = async (
    transactionId: string,
    payload: TransactionCreatePayload,
    currentTransaction: Transaction,
  ) => {
    setNotice(null);

    try {
      const transaction = await updateTransaction(workspaceId, transactionId, {
        ...payload,
        paid_by_user_id: currentTransaction.paid_by_user_id,
        split_config: currentTransaction.split_config,
      });
      syncTransaction(transaction);
      setNotice({ type: "success", message: "Movimiento actualizado." });
      setEditingTransactionId(null);
      setExpandedTransactionId(transactionId);
      await loadPanelData();
      onTransactionsChanged?.();
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleDelete = async (transaction: Transaction) => {
    const shouldDelete = window.confirm(
      `Vas a eliminar el movimiento ${getTransactionHeadline(transaction)}. Esta accion actualizara los saldos afectados.`,
    );

    if (!shouldDelete) {
      return;
    }

    setNotice(null);

    try {
      await deleteTransaction(workspaceId, transaction.id);
      setTransactions((currentTransactions) =>
        currentTransactions.filter((currentTransaction) => currentTransaction.id !== transaction.id),
      );
      setTransactionDetails((currentDetails) => {
        const nextDetails = { ...currentDetails };
        delete nextDetails[transaction.id];
        return nextDetails;
      });
      if (expandedTransactionId === transaction.id) {
        setExpandedTransactionId(null);
      }
      if (editingTransactionId === transaction.id) {
        setEditingTransactionId(null);
      }
      setNotice({ type: "success", message: "Movimiento eliminado." });
      await loadPanelData();
      onTransactionsChanged?.();
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  return (
    <section className="workspace-panel">
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Movimientos</h2>
        <p className="workspace-section-copy">
          Registra ingresos, gastos y transferencias con detalle inline y orden cronologico.
        </p>
      </div>

      {notice ? (
        <div
          className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
          role={notice.type === "error" ? "alert" : "status"}
        >
          {notice.message}
        </div>
      ) : null}

      <div className="entity-section">
        <div className="workspace-form-header">
          <h3 className="workspace-section-title">Nuevo movimiento</h3>
          <p className="workspace-section-copy">
            La moneda se resuelve desde las cuentas seleccionadas y las transferencias quedan separadas.
          </p>
        </div>
        <TransactionForm
          accounts={formAccounts}
          allowReceiptUpload
          categories={formCategories}
          members={members}
          defaultValues={DEFAULT_TRANSACTION_FORM_VALUES}
          fieldIdPrefix={`transaction-create-${workspaceId}`}
          onSubmitTransaction={handleCreate}
          resetOnSuccess
          submitLabel="Guardar movimiento"
          submittingLabel="Guardando..."
        />
      </div>

      <div className="entity-list" aria-label="Historial de movimientos del espacio">
        {isLoading ? <p className="workspace-section-copy">Cargando movimientos...</p> : null}

        {!isLoading && transactions.length === 0 ? (
          <p className="workspace-section-copy">
            Todavia no hay movimientos. Registra el primero para empezar a construir el historial.
          </p>
        ) : null}

        {!isLoading
          ? transactions.map((transaction) => {
              const detailTransaction = transactionDetails[transaction.id] ?? transaction;
              const isExpanded = expandedTransactionId === transaction.id;
              const isEditing = editingTransactionId === transaction.id;
              const isLoadingDetail = loadingTransactionId === transaction.id;
              const receiptKind = getTransactionReceiptKind(detailTransaction.receipt_url);

              return (
                <article key={transaction.id} className="entity-card transaction-card">
                  <div className="entity-card-header">
                    <div>
                      <div className="workspace-list-topline">
                        <strong>{getTransactionHeadline(transaction)}</strong>
                        {transaction.receipt_url ? (
                          <span aria-label="Movimiento con recibo adjunto" title="Movimiento con recibo adjunto">
                            📎
                          </span>
                        ) : null}
                        <span className={`workspace-role-chip transaction-type-chip transaction-type-chip-${transaction.type}`}>
                          {TRANSACTION_TYPE_LABELS[transaction.type]}
                        </span>
                      </div>
                      <p className="workspace-section-copy">{getTransactionMetaLabel(transaction)}</p>
                      <p className="workspace-section-copy">{getTransactionRouteLabel(transaction)}</p>
                    </div>
                    <div className="entity-card-side">
                      <span className={`account-balance transaction-amount transaction-amount-${transaction.type}`}>
                        {formatTransactionAmount(transaction)}
                      </span>
                      <span className="workspace-member-date">{transaction.currency}</span>
                    </div>
                  </div>

                  <div className="entity-actions">
                    <button
                      className="secondary-action entity-secondary-action"
                      onClick={() => {
                        void handleOpenDetail(transaction.id);
                      }}
                      type="button"
                    >
                      {isExpanded ? "Ocultar detalle" : "Ver detalle"}
                    </button>
                    <button
                      className="secondary-action entity-secondary-action"
                      onClick={() => {
                        void handleOpenEdit(transaction.id);
                      }}
                      type="button"
                    >
                      {isEditing ? "Cerrar edicion" : "Editar"}
                    </button>
                    <button
                      className="secondary-action entity-danger-action"
                      onClick={() => {
                        void handleDelete(transaction);
                      }}
                      type="button"
                    >
                      Eliminar
                    </button>
                  </div>

                  {isExpanded ? (
                    <div className="entity-inline-form transaction-detail-panel">
                      {isLoadingDetail ? <p className="workspace-section-copy">Cargando detalle...</p> : null}

                      {!isLoadingDetail ? (
                        <dl className="transaction-detail-grid">
                          <div>
                            <dt>Tipo</dt>
                            <dd>{TRANSACTION_TYPE_LABELS[detailTransaction.type]}</dd>
                          </div>
                          <div>
                            <dt>Importe</dt>
                            <dd>{formatTransactionAmount(detailTransaction)}</dd>
                          </div>
                          <div>
                            <dt>Fecha</dt>
                            <dd>{formatTransactionOccurredAt(detailTransaction.occurred_at)}</dd>
                          </div>
                          <div>
                            <dt>Origen</dt>
                            <dd>{detailTransaction.source_account?.name ?? "-"}</dd>
                          </div>
                          <div>
                            <dt>Destino</dt>
                            <dd>{detailTransaction.destination_account?.name ?? "-"}</dd>
                          </div>
                          <div>
                            <dt>Categoria</dt>
                            <dd>{detailTransaction.category?.name ?? "No aplica"}</dd>
                          </div>
                          <div>
                            <dt>Pagado por</dt>
                            <dd>{detailTransaction.paid_by_user?.email ?? "Sesion actual"}</dd>
                          </div>
                          <div>
                            <dt>Descripcion</dt>
                            <dd>{detailTransaction.description ?? "Sin detalle adicional"}</dd>
                          </div>
                          <div>
                            <dt>Recibo</dt>
                            <dd>
                              {detailTransaction.receipt_url ? (
                                receiptKind === "image" ? (
                                  <div>
                                    <a href={detailTransaction.receipt_url} target="_blank" rel="noreferrer">
                                      Abrir recibo
                                    </a>
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                    <img
                                      src={detailTransaction.receipt_url}
                                      alt="Recibo adjunto del movimiento"
                                    />
                                  </div>
                                ) : receiptKind === "pdf" ? (
                                  <a href={detailTransaction.receipt_url} target="_blank" rel="noreferrer">
                                    Abrir recibo PDF
                                  </a>
                                ) : (
                                  <a href={detailTransaction.receipt_url} target="_blank" rel="noreferrer">
                                    Descargar recibo
                                  </a>
                                )
                              ) : (
                                "Sin recibo adjunto"
                              )}
                            </dd>
                          </div>
                        </dl>
                      ) : null}

                      {isEditing && !isLoadingDetail ? (
                        <div className="entity-inline-form">
                          <div className="workspace-form-header">
                            <h3 className="workspace-section-title">Editar movimiento</h3>
                            <p className="workspace-section-copy">
                              Actualiza el movimiento sin salir del historial y refresca los saldos afectados.
                            </p>
                          </div>
                          <TransactionForm
                            accounts={formAccounts}
                            categories={formCategories}
                            members={members}
                            defaultValues={toTransactionFormDefaults(detailTransaction)}
                            fieldIdPrefix={`transaction-edit-${transaction.id}`}
                            onCancel={() => setEditingTransactionId(null)}
                            onSubmitTransaction={(payload) => handleUpdate(transaction.id, payload, detailTransaction)}
                            submitLabel="Guardar cambios"
                            submittingLabel="Guardando..."
                          />
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </article>
              );
            })
          : null}
      </div>
    </section>
  );
}
