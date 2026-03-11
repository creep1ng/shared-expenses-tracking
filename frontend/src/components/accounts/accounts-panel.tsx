"use client";

import React from "react";
import { useEffect, useState } from "react";

import { AccountForm, DEFAULT_ACCOUNT_FORM_VALUES } from "@/components/accounts/account-form";
import { getErrorMessage } from "@/lib/auth/errors";
import { archiveAccount, createAccount, listAccounts, updateAccount } from "@/lib/accounts/api";
import {
  ACCOUNT_TYPE_LABELS,
  formatMinorUnitsAsCurrency,
  formatMinorUnitsForInput,
} from "@/lib/accounts/presentation";
import type { Account, AccountCreatePayload } from "@/lib/accounts/types";

type AccountsPanelProps = {
  workspaceId: string;
  refreshNonce?: number;
};

type Notice = {
  type: "error" | "success";
  message: string;
};

function toAccountFormDefaults(account: Account) {
  return {
    name: account.name,
    type: account.type,
    currency: account.currency,
    initialBalance: formatMinorUnitsForInput(account.initial_balance_minor),
    description: account.description ?? "",
  } as const;
}

export function AccountsPanel({ workspaceId, refreshNonce = 0 }: AccountsPanelProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);

  const loadAccounts = React.useCallback(async () => {
    setIsLoading(true);

    try {
      const response = await listAccounts(workspaceId);
      setAccounts(response.accounts);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    setEditingAccountId(null);
    setNotice(null);
  }, [workspaceId]);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts, refreshNonce]);

  const handleCreate = async (payload: AccountCreatePayload) => {
    setNotice(null);

    try {
      const account = await createAccount(workspaceId, payload);
      setAccounts((currentAccounts) => [account, ...currentAccounts]);
      setNotice({ type: "success", message: `Cuenta ${account.name} creada correctamente.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleUpdate = async (accountId: string, payload: AccountCreatePayload) => {
    setNotice(null);

    try {
      const updatedAccount = await updateAccount(workspaceId, accountId, payload);
      setAccounts((currentAccounts) =>
        currentAccounts.map((account) => (account.id === updatedAccount.id ? updatedAccount : account)),
      );
      setNotice({ type: "success", message: `Cuenta ${updatedAccount.name} actualizada.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleArchive = async (account: Account) => {
    const shouldArchive = window.confirm(
      `Vas a archivar la cuenta ${account.name}. Seguira visible en el historial, pero dejara de aparecer como activa.`,
    );

    if (!shouldArchive) {
      return;
    }

    setNotice(null);

    try {
      const archivedAccount = await archiveAccount(workspaceId, account.id);
      setAccounts((currentAccounts) =>
        currentAccounts.filter((currentAccount) => currentAccount.id !== archivedAccount.id),
      );
      if (editingAccountId === archivedAccount.id) {
        setEditingAccountId(null);
      }
      setNotice({ type: "success", message: `Cuenta ${archivedAccount.name} archivada.` });
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  return (
    <section className="workspace-panel">
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Cuentas</h2>
        <p className="workspace-section-copy">
          Gestiona las cuentas activas del espacio y revisa su saldo actual en una sola vista.
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
          <h3 className="workspace-section-title">Nueva cuenta</h3>
          <p className="workspace-section-copy">
            Registra efectivo, bancos, ahorros o tarjetas con su saldo inicial en moneda ISO.
          </p>
        </div>
        <AccountForm
          defaultValues={DEFAULT_ACCOUNT_FORM_VALUES}
          fieldIdPrefix={`account-create-${workspaceId}`}
          onSubmitAccount={handleCreate}
          resetOnSuccess
          submitLabel="Crear cuenta"
          submittingLabel="Guardando..."
        />
      </div>

      <div className="entity-list" aria-label="Cuentas activas del espacio">
        {isLoading ? <p className="workspace-section-copy">Cargando cuentas...</p> : null}

        {!isLoading && accounts.length === 0 ? (
          <p className="workspace-section-copy">
            Todavia no hay cuentas activas. Crea la primera para empezar a registrar movimientos.
          </p>
        ) : null}

        {!isLoading
          ? accounts.map((account) => {
              const isEditing = editingAccountId === account.id;

              return (
                <article key={account.id} className="entity-card">
                  <div className="entity-card-header">
                    <div>
                      <div className="workspace-list-topline">
                        <strong>{account.name}</strong>
                        <span className="workspace-role-chip">{ACCOUNT_TYPE_LABELS[account.type]}</span>
                      </div>
                      <p className="workspace-section-copy">
                        {account.currency} · Saldo inicial {formatMinorUnitsAsCurrency(account.initial_balance_minor, account.currency)}
                      </p>
                    </div>
                    <div className="entity-card-side">
                      <span className="account-balance">
                        {formatMinorUnitsAsCurrency(account.current_balance_minor, account.currency)}
                      </span>
                      <span className="workspace-member-date">Saldo actual</span>
                    </div>
                  </div>

                  {account.description ? <p className="workspace-section-copy">{account.description}</p> : null}

                  <div className="entity-actions">
                    <button
                      className="secondary-action entity-secondary-action"
                      onClick={() => setEditingAccountId(isEditing ? null : account.id)}
                      type="button"
                    >
                      {isEditing ? "Cerrar edicion" : "Editar"}
                    </button>
                    <button
                      className="secondary-action entity-danger-action"
                      onClick={() => {
                        void handleArchive(account);
                      }}
                      type="button"
                    >
                      Archivar
                    </button>
                  </div>

                  {isEditing ? (
                    <div className="entity-inline-form">
                      <div className="workspace-form-header">
                        <h3 className="workspace-section-title">Editar cuenta</h3>
                        <p className="workspace-section-copy">
                          Actualiza el nombre, el tipo o el saldo base sin salir del tablero.
                        </p>
                      </div>
                      <AccountForm
                        defaultValues={toAccountFormDefaults(account)}
                        fieldIdPrefix={`account-edit-${account.id}`}
                        onCancel={() => setEditingAccountId(null)}
                        onSubmitAccount={(payload) => handleUpdate(account.id, payload)}
                        submitLabel="Guardar cambios"
                        submittingLabel="Guardando..."
                      />
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
