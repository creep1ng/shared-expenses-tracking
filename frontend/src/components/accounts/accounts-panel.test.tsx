import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountsPanel } from "@/components/accounts/accounts-panel";

const archiveAccountMock = vi.fn();
const createAccountMock = vi.fn();
const listAccountsMock = vi.fn();
const updateAccountMock = vi.fn();

vi.mock("@/lib/accounts/api", () => ({
  archiveAccount: (...args: unknown[]) => archiveAccountMock(...args),
  createAccount: (...args: unknown[]) => createAccountMock(...args),
  listAccounts: (...args: unknown[]) => listAccountsMock(...args),
  updateAccount: (...args: unknown[]) => updateAccountMock(...args),
}));

describe("AccountsPanel", () => {
  const confirmSpy = vi.spyOn(window, "confirm");

  beforeEach(() => {
    archiveAccountMock.mockReset();
    createAccountMock.mockReset();
    listAccountsMock.mockReset();
    updateAccountMock.mockReset();
    confirmSpy.mockReset();
  });

  it("loads active accounts and shows current balances", async () => {
    listAccountsMock.mockResolvedValue({
      accounts: [
        {
          id: "acc-1",
          workspace_id: "workspace-1",
          name: "Cuenta principal",
          type: "bank_account",
          currency: "EUR",
          initial_balance_minor: 120000,
          current_balance_minor: 98550,
          description: "Uso diario",
          archived_at: null,
          is_archived: false,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
      ],
    });

    render(<AccountsPanel workspaceId="workspace-1" />);

    expect(await screen.findByText("Cuenta principal")).toBeInTheDocument();
    expect(screen.getAllByText("Cuenta bancaria")[0]).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("985,50") && content.includes("€"))).toBeInTheDocument();
    expect(listAccountsMock).toHaveBeenCalledWith("workspace-1");
  });

  it("creates, edits and archives accounts", async () => {
    const user = userEvent.setup();

    listAccountsMock.mockResolvedValue({
      accounts: [
        {
          id: "acc-1",
          workspace_id: "workspace-1",
          name: "Cuenta principal",
          type: "bank_account",
          currency: "EUR",
          initial_balance_minor: 120000,
          current_balance_minor: 120000,
          description: null,
          archived_at: null,
          is_archived: false,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
      ],
    });
    createAccountMock.mockResolvedValue({
      id: "acc-2",
      workspace_id: "workspace-1",
      name: "Tarjeta viaje",
      type: "credit_card",
      currency: "USD",
      initial_balance_minor: -4550,
      current_balance_minor: -4550,
      description: "Reserva hotel",
      archived_at: null,
      is_archived: false,
      created_at: "2026-03-08T10:00:00Z",
      updated_at: "2026-03-08T10:00:00Z",
    });
    updateAccountMock.mockResolvedValue({
      id: "acc-1",
      workspace_id: "workspace-1",
      name: "Cuenta hogar",
      type: "savings_account",
      currency: "EUR",
      initial_balance_minor: 200000,
      current_balance_minor: 200000,
      description: "Ahorro comun",
      archived_at: null,
      is_archived: false,
      created_at: "2026-03-08T10:00:00Z",
      updated_at: "2026-03-08T11:00:00Z",
    });
    archiveAccountMock.mockResolvedValue({ id: "acc-1", name: "Cuenta hogar" });
    confirmSpy.mockReturnValue(true);

    render(<AccountsPanel workspaceId="workspace-1" />);

    await screen.findByText("Cuenta principal");

    await user.clear(screen.getByLabelText(/^Nombre$/i));
    await user.type(screen.getByLabelText(/^Nombre$/i), "Tarjeta viaje");
    await user.selectOptions(screen.getByLabelText(/^Tipo$/i), "credit_card");
    await user.clear(screen.getByLabelText(/^Moneda$/i));
    await user.type(screen.getByLabelText(/^Moneda$/i), "usd");
    await user.clear(screen.getByLabelText(/^Saldo inicial$/i));
    await user.type(screen.getByLabelText(/^Saldo inicial$/i), "-45.50");
    await user.clear(screen.getByLabelText(/^Descripcion$/i));
    await user.type(screen.getByLabelText(/^Descripcion$/i), "Reserva hotel");
    await user.click(screen.getByRole("button", { name: /crear cuenta/i }));

    await waitFor(() => {
      expect(createAccountMock).toHaveBeenCalledWith("workspace-1", {
        name: "Tarjeta viaje",
        type: "credit_card",
        currency: "USD",
        initial_balance_minor: -4550,
        description: "Reserva hotel",
      });
    });

    expect(await screen.findByText("Tarjeta viaje")).toBeInTheDocument();

    const originalAccountCard = screen.getByText("Cuenta principal").closest("article");

    expect(originalAccountCard).not.toBeNull();

    await user.click(within(originalAccountCard as HTMLElement).getByRole("button", { name: /editar/i }));

    const editNameInput = screen.getByLabelText("Nombre", { selector: "input[id='account-edit-acc-1-name']" });
    const editTypeSelect = screen.getByLabelText("Tipo", { selector: "select[id='account-edit-acc-1-type']" });
    const editBalanceInput = screen.getByLabelText("Saldo inicial", {
      selector: "input[id='account-edit-acc-1-initial-balance']",
    });
    const editDescriptionInput = screen.getByLabelText("Descripcion", {
      selector: "textarea[id='account-edit-acc-1-description']",
    });

    await user.clear(editNameInput);
    await user.type(editNameInput, "Cuenta hogar");
    await user.selectOptions(editTypeSelect, "savings_account");
    await user.clear(editBalanceInput);
    await user.type(editBalanceInput, "2000.00");
    await user.clear(editDescriptionInput);
    await user.type(editDescriptionInput, "Ahorro comun");
    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    await waitFor(() => {
      expect(updateAccountMock).toHaveBeenCalledWith("workspace-1", "acc-1", {
        name: "Cuenta hogar",
        type: "savings_account",
        currency: "EUR",
        initial_balance_minor: 200000,
        description: "Ahorro comun",
      });
    });

    expect(await screen.findByText("Cuenta hogar")).toBeInTheDocument();

    const updatedAccountCard = screen.getByText("Cuenta hogar").closest("article");

    expect(updatedAccountCard).not.toBeNull();

    await user.click(within(updatedAccountCard as HTMLElement).getByRole("button", { name: /archivar/i }));

    await waitFor(() => {
      expect(archiveAccountMock).toHaveBeenCalledWith("workspace-1", "acc-1");
    });
    expect(screen.queryByText("Cuenta hogar")).not.toBeInTheDocument();
  });

  it("reloads balances when the refresh nonce changes", async () => {
    listAccountsMock
      .mockResolvedValueOnce({
        accounts: [
          {
            id: "acc-1",
            workspace_id: "workspace-1",
            name: "Cuenta principal",
            type: "bank_account",
            currency: "EUR",
            initial_balance_minor: 120000,
            current_balance_minor: 98550,
            description: "Uso diario",
            archived_at: null,
            is_archived: false,
            created_at: "2026-03-08T10:00:00Z",
            updated_at: "2026-03-08T10:00:00Z",
          },
        ],
      })
      .mockResolvedValueOnce({
        accounts: [
          {
            id: "acc-1",
            workspace_id: "workspace-1",
            name: "Cuenta principal",
            type: "bank_account",
            currency: "EUR",
            initial_balance_minor: 120000,
            current_balance_minor: 101050,
            description: "Uso diario",
            archived_at: null,
            is_archived: false,
            created_at: "2026-03-08T10:00:00Z",
            updated_at: "2026-03-08T10:05:00Z",
          },
        ],
      });

    const { rerender } = render(<AccountsPanel workspaceId="workspace-1" refreshNonce={0} />);

    expect(await screen.findByText((content) => content.includes("985,50") && content.includes("€"))).toBeInTheDocument();

    rerender(<AccountsPanel workspaceId="workspace-1" refreshNonce={1} />);

    expect(await screen.findByText((content) => content.includes("1010,50") && content.includes("€"))).toBeInTheDocument();
    expect(listAccountsMock).toHaveBeenCalledTimes(2);
  });
});
