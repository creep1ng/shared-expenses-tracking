import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TransactionsPanel } from "@/components/transactions/transactions-panel";

const createTransactionMock = vi.fn();
const deleteTransactionMock = vi.fn();
const getTransactionMock = vi.fn();
const listTransactionsMock = vi.fn();
const updateTransactionMock = vi.fn();
const listAccountsMock = vi.fn();
const listCategoriesMock = vi.fn();

vi.mock("@/lib/transactions/api", () => ({
  createTransaction: (...args: unknown[]) => createTransactionMock(...args),
  deleteTransaction: (...args: unknown[]) => deleteTransactionMock(...args),
  getTransaction: (...args: unknown[]) => getTransactionMock(...args),
  listTransactions: (...args: unknown[]) => listTransactionsMock(...args),
  updateTransaction: (...args: unknown[]) => updateTransactionMock(...args),
}));

vi.mock("@/lib/accounts/api", () => ({
  listAccounts: (...args: unknown[]) => listAccountsMock(...args),
}));

vi.mock("@/lib/categories/api", () => ({
  listCategories: (...args: unknown[]) => listCategoriesMock(...args),
}));

const accounts = [
  {
    id: "acc-1",
    workspace_id: "workspace-1",
    name: "Cuenta principal",
    type: "bank_account" as const,
    currency: "EUR",
    initial_balance_minor: 100000,
    current_balance_minor: 100000,
    description: null,
    archived_at: null,
    is_archived: false,
    created_at: "2026-03-10T10:00:00Z",
    updated_at: "2026-03-10T10:00:00Z",
  },
  {
    id: "acc-2",
    workspace_id: "workspace-1",
    name: "Ahorro viaje",
    type: "savings_account" as const,
    currency: "EUR",
    initial_balance_minor: 20000,
    current_balance_minor: 20000,
    description: null,
    archived_at: null,
    is_archived: false,
    created_at: "2026-03-10T10:00:00Z",
    updated_at: "2026-03-10T10:00:00Z",
  },
];

const categories = [
  {
    id: "cat-1",
    workspace_id: "workspace-1",
    name: "Nomina",
    type: "income" as const,
    icon: "briefcase",
    color: "#2563EB",
    archived_at: null,
    is_archived: false,
    created_at: "2026-03-10T10:00:00Z",
    updated_at: "2026-03-10T10:00:00Z",
  },
  {
    id: "cat-2",
    workspace_id: "workspace-1",
    name: "Supermercado",
    type: "expense" as const,
    icon: "shopping-cart",
    color: "#D97706",
    archived_at: null,
    is_archived: false,
    created_at: "2026-03-10T10:00:00Z",
    updated_at: "2026-03-10T10:00:00Z",
  },
];

const incomeTransaction = {
  id: "tx-1",
  workspace_id: "workspace-1",
  type: "income" as const,
  source_account_id: null,
  destination_account_id: "acc-1",
  category_id: "cat-1",
  paid_by_user_id: "user-1",
  amount_minor: 250000,
  currency: "EUR",
  description: "Nomina marzo",
  occurred_at: "2026-03-10T08:00:00Z",
  split_config: null,
  source_account: null,
  destination_account: {
    id: "acc-1",
    workspace_id: "workspace-1",
    name: "Cuenta principal",
    type: "bank_account" as const,
    currency: "EUR",
    archived_at: null,
    is_archived: false,
  },
  category: {
    id: "cat-1",
    workspace_id: "workspace-1",
    name: "Nomina",
    type: "income" as const,
    archived_at: null,
    is_archived: false,
  },
  paid_by_user: { id: "user-1", email: "owner@example.com" },
  created_at: "2026-03-10T08:00:00Z",
  updated_at: "2026-03-10T08:00:00Z",
};

const transferTransaction = {
  id: "tx-2",
  workspace_id: "workspace-1",
  type: "transfer" as const,
  source_account_id: "acc-1",
  destination_account_id: "acc-2",
  category_id: null,
  paid_by_user_id: null,
  amount_minor: 5000,
  currency: "EUR",
  description: "Traspaso ahorro",
  occurred_at: "2026-03-11T09:30:00Z",
  split_config: null,
  source_account: {
    id: "acc-1",
    workspace_id: "workspace-1",
    name: "Cuenta principal",
    type: "bank_account" as const,
    currency: "EUR",
    archived_at: null,
    is_archived: false,
  },
  destination_account: {
    id: "acc-2",
    workspace_id: "workspace-1",
    name: "Ahorro viaje",
    type: "savings_account" as const,
    currency: "EUR",
    archived_at: null,
    is_archived: false,
  },
  category: null,
  paid_by_user: null,
  created_at: "2026-03-11T09:30:00Z",
  updated_at: "2026-03-11T09:30:00Z",
};

function formatDateForInput(value: Date): string {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, "0");
  const day = `${value.getDate()}`.padStart(2, "0");
  const hours = `${value.getHours()}`.padStart(2, "0");
  const minutes = `${value.getMinutes()}`.padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

describe("TransactionsPanel", () => {
  const confirmSpy = vi.spyOn(window, "confirm");

  beforeEach(() => {
    createTransactionMock.mockReset();
    deleteTransactionMock.mockReset();
    getTransactionMock.mockReset();
    listTransactionsMock.mockReset();
    updateTransactionMock.mockReset();
    listAccountsMock.mockReset();
    listCategoriesMock.mockReset();
    confirmSpy.mockReset();

    listAccountsMock.mockResolvedValue({ accounts });
    listCategoriesMock.mockResolvedValue({ categories });
    listTransactionsMock.mockResolvedValue({ transactions: [transferTransaction, incomeTransaction] });
    getTransactionMock.mockImplementation(async (_workspaceId: string, transactionId: string) =>
      transactionId === "tx-2" ? transferTransaction : incomeTransaction,
    );
  });

  it("shows movements in chronological order and renders transfer badges", async () => {
    render(<TransactionsPanel workspaceId="workspace-1" />);

    expect(await screen.findByText("Traspaso ahorro")).toBeInTheDocument();
    const cards = screen.getAllByRole("article");

    expect(within(cards[0]).getByText("Transferencia")).toBeInTheDocument();
    expect(within(cards[0]).getByText("Cuenta principal -> Ahorro viaje")).toBeInTheDocument();
    expect(within(cards[1]).getByText("Ingreso")).toBeInTheDocument();
  });

  it("creates an expense and keeps backend payload shape", async () => {
    const user = userEvent.setup();
    const onTransactionsChanged = vi.fn();
    const today = new Date();
    const validDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 8, 45);

    createTransactionMock.mockResolvedValue({
      ...incomeTransaction,
      id: "tx-3",
      type: "expense",
      source_account_id: "acc-1",
      destination_account_id: null,
      category_id: "cat-2",
      amount_minor: 1250,
      description: "Cafe oficina",
      occurred_at: validDate.toISOString(),
      source_account: incomeTransaction.destination_account,
      destination_account: null,
      category: {
        id: "cat-2",
        workspace_id: "workspace-1",
        name: "Supermercado",
        type: "expense" as const,
        archived_at: null,
        is_archived: false,
      },
    });

    render(<TransactionsPanel workspaceId="workspace-1" onTransactionsChanged={onTransactionsChanged} />);

    await screen.findByText("Traspaso ahorro");

    await user.clear(screen.getByLabelText(/^Importe$/i));
    await user.type(screen.getByLabelText(/^Importe$/i), "12.50");
    await user.selectOptions(screen.getByLabelText(/^Cuenta de origen$/i), "acc-1");
    await user.selectOptions(screen.getByLabelText(/^Categoria$/i), "cat-2");
    await user.clear(screen.getByLabelText(/^Descripcion$/i));
    await user.type(screen.getByLabelText(/^Descripcion$/i), "Cafe oficina");
    await user.clear(screen.getByLabelText(/^Fecha y hora$/i));
    await user.type(screen.getByLabelText(/^Fecha y hora$/i), formatDateForInput(validDate));
    await user.click(screen.getByRole("button", { name: /guardar movimiento/i }));

    await waitFor(() => {
      expect(createTransactionMock).toHaveBeenCalledWith("workspace-1", {
        type: "expense",
        source_account_id: "acc-1",
        destination_account_id: null,
        category_id: "cat-2",
        paid_by_user_id: null,
        amount_minor: 1250,
        currency: "EUR",
        description: "Cafe oficina",
        occurred_at: validDate.toISOString(),
        split_config: null,
      });
    });

    expect(onTransactionsChanged).toHaveBeenCalledTimes(1);
  });

  it("loads detail inline and edits an existing transaction", async () => {
    const user = userEvent.setup();
    const onTransactionsChanged = vi.fn();

    updateTransactionMock.mockResolvedValue({
      ...incomeTransaction,
      amount_minor: 275000,
      description: "Nomina marzo actualizada",
      occurred_at: "2026-03-10T10:15:00Z",
    });

    render(<TransactionsPanel workspaceId="workspace-1" onTransactionsChanged={onTransactionsChanged} />);

    const incomeCard = (await screen.findByText("Nomina marzo")).closest("article");

    expect(incomeCard).not.toBeNull();

    await user.click(within(incomeCard as HTMLElement).getByRole("button", { name: /ver detalle/i }));

    expect(await screen.findByText("Pagado por")).toBeInTheDocument();
    expect(screen.getByText("owner@example.com")).toBeInTheDocument();

    await user.click(within(incomeCard as HTMLElement).getByRole("button", { name: /^editar$/i }));

    const amountInput = screen.getByLabelText("Importe", {
      selector: "input[id='transaction-edit-tx-1-amount']",
    });
    const descriptionInput = screen.getByLabelText("Descripcion", {
      selector: "textarea[id='transaction-edit-tx-1-description']",
    });
    const occurredAtInput = screen.getByLabelText("Fecha y hora", {
      selector: "input[id='transaction-edit-tx-1-occurred-at']",
    });

    await user.clear(amountInput);
    await user.type(amountInput, "2750.00");
    await user.clear(descriptionInput);
    await user.type(descriptionInput, "Nomina marzo actualizada");
    await user.clear(occurredAtInput);
    await user.type(occurredAtInput, "2026-03-10T11:15");
    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    await waitFor(() => {
      expect(updateTransactionMock).toHaveBeenCalledWith("workspace-1", "tx-1", {
        type: "income",
        source_account_id: null,
        destination_account_id: "acc-1",
        category_id: "cat-1",
        paid_by_user_id: "user-1",
        amount_minor: 275000,
        currency: "EUR",
        description: "Nomina marzo actualizada",
        occurred_at: new Date("2026-03-10T11:15").toISOString(),
        split_config: null,
      });
    });

    expect(onTransactionsChanged).toHaveBeenCalledTimes(1);
  });

  it("validates transfers, hides category field and deletes with confirmation", async () => {
    const user = userEvent.setup();
    const onTransactionsChanged = vi.fn();

    deleteTransactionMock.mockResolvedValue(undefined);
    confirmSpy.mockReturnValue(true);

    render(<TransactionsPanel workspaceId="workspace-1" onTransactionsChanged={onTransactionsChanged} />);

    await screen.findByText("Traspaso ahorro");

    await user.selectOptions(screen.getByLabelText(/tipo de movimiento/i), "transfer");

    expect(screen.queryByLabelText(/^Categoria$/i)).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText(/^Cuenta de origen$/i), "acc-1");
    await user.selectOptions(screen.getByLabelText(/^Cuenta de destino$/i), "acc-1");
    await user.click(screen.getByRole("button", { name: /guardar movimiento/i }));

    expect(await screen.findByText(/la transferencia debe usar cuentas distintas/i)).toBeInTheDocument();
    expect(createTransactionMock).not.toHaveBeenCalled();

    const transferCard = screen.getByText("Traspaso ahorro").closest("article");

    expect(transferCard).not.toBeNull();

    await user.click(within(transferCard as HTMLElement).getByRole("button", { name: /eliminar/i }));

    await waitFor(() => {
      expect(deleteTransactionMock).toHaveBeenCalledWith("workspace-1", "tx-2");
    });

    expect(onTransactionsChanged).toHaveBeenCalledTimes(1);
  });
});
