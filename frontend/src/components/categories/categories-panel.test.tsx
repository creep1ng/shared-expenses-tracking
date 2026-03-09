import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CategoriesPanel } from "@/components/categories/categories-panel";

const archiveCategoryMock = vi.fn();
const createCategoryMock = vi.fn();
const listCategoriesMock = vi.fn();
const updateCategoryMock = vi.fn();

vi.mock("@/lib/categories/api", () => ({
  archiveCategory: (...args: unknown[]) => archiveCategoryMock(...args),
  createCategory: (...args: unknown[]) => createCategoryMock(...args),
  listCategories: (...args: unknown[]) => listCategoriesMock(...args),
  updateCategory: (...args: unknown[]) => updateCategoryMock(...args),
}));

describe("CategoriesPanel", () => {
  const confirmSpy = vi.spyOn(window, "confirm");

  beforeEach(() => {
    archiveCategoryMock.mockReset();
    createCategoryMock.mockReset();
    listCategoriesMock.mockReset();
    updateCategoryMock.mockReset();
    confirmSpy.mockReset();
  });

  it("loads active categories only by default", async () => {
    listCategoriesMock.mockResolvedValue({
      categories: [
        {
          id: "cat-1",
          workspace_id: "workspace-1",
          name: "Comida",
          type: "expense",
          icon: "utensils-crossed",
          color: "#D97706",
          archived_at: null,
          is_archived: false,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
        {
          id: "cat-2",
          workspace_id: "workspace-1",
          name: "Archivada",
          type: "expense",
          icon: "archive",
          color: "#111111",
          archived_at: "2026-03-08T10:00:00Z",
          is_archived: true,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
      ],
    });

    render(<CategoriesPanel workspaceId="workspace-1" />);

    expect(await screen.findByText("Comida")).toBeInTheDocument();
    expect(screen.queryByText("Archivada")).not.toBeInTheDocument();
    expect(listCategoriesMock).toHaveBeenCalledWith("workspace-1");
  });

  it("creates, edits and archives categories", async () => {
    const user = userEvent.setup();

    listCategoriesMock.mockResolvedValue({
      categories: [
        {
          id: "cat-1",
          workspace_id: "workspace-1",
          name: "Comida",
          type: "expense",
          icon: "utensils-crossed",
          color: "#D97706",
          archived_at: null,
          is_archived: false,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
      ],
    });
    createCategoryMock.mockResolvedValue({
      id: "cat-2",
      workspace_id: "workspace-1",
      name: "Mascotas",
      type: "expense",
      icon: "paw-print",
      color: "#7C3AED",
      archived_at: null,
      is_archived: false,
      created_at: "2026-03-08T10:00:00Z",
      updated_at: "2026-03-08T10:00:00Z",
    });
    updateCategoryMock.mockResolvedValue({
      id: "cat-1",
      workspace_id: "workspace-1",
      name: "Supermercado",
      type: "expense",
      icon: "shopping-basket",
      color: "#2563EB",
      archived_at: null,
      is_archived: false,
      created_at: "2026-03-08T10:00:00Z",
      updated_at: "2026-03-08T11:00:00Z",
    });
    archiveCategoryMock.mockResolvedValue({ id: "cat-1", name: "Supermercado" });
    confirmSpy.mockReturnValue(true);

    render(<CategoriesPanel workspaceId="workspace-1" />);

    await screen.findByText("Comida");

    await user.clear(screen.getByLabelText(/^Nombre$/i));
    await user.type(screen.getByLabelText(/^Nombre$/i), "Mascotas");
    await user.clear(screen.getByLabelText(/^Icono$/i));
    await user.type(screen.getByLabelText(/^Icono$/i), "paw-print");
    await user.clear(screen.getByLabelText(/^Color$/i));
    await user.type(screen.getByLabelText(/^Color$/i), "#7c3aed");
    await user.click(screen.getByRole("button", { name: /crear categoria/i }));

    await waitFor(() => {
      expect(createCategoryMock).toHaveBeenCalledWith("workspace-1", {
        name: "Mascotas",
        type: "expense",
        icon: "paw-print",
        color: "#7C3AED",
      });
    });

    expect(await screen.findByText("Mascotas")).toBeInTheDocument();

    const originalCategoryCard = screen.getByText("Comida").closest("article");

    expect(originalCategoryCard).not.toBeNull();

    await user.click(within(originalCategoryCard as HTMLElement).getByRole("button", { name: /editar/i }));

    const editNameInput = screen.getByLabelText("Nombre", { selector: "input[id='category-edit-cat-1-name']" });
    const editIconInput = screen.getByLabelText("Icono", { selector: "input[id='category-edit-cat-1-icon']" });
    const editColorInput = screen.getByLabelText("Color", { selector: "input[id='category-edit-cat-1-color']" });

    await user.clear(editNameInput);
    await user.type(editNameInput, "Supermercado");
    await user.clear(editIconInput);
    await user.type(editIconInput, "shopping-basket");
    await user.clear(editColorInput);
    await user.type(editColorInput, "#2563eb");
    await user.click(screen.getByRole("button", { name: /guardar cambios/i }));

    await waitFor(() => {
      expect(updateCategoryMock).toHaveBeenCalledWith("workspace-1", "cat-1", {
        name: "Supermercado",
        type: "expense",
        icon: "shopping-basket",
        color: "#2563EB",
      });
    });

    expect(await screen.findByText("Supermercado")).toBeInTheDocument();

    const updatedCategoryCard = screen.getByText("Supermercado").closest("article");

    expect(updatedCategoryCard).not.toBeNull();

    await user.click(within(updatedCategoryCard as HTMLElement).getByRole("button", { name: /archivar/i }));

    await waitFor(() => {
      expect(archiveCategoryMock).toHaveBeenCalledWith("workspace-1", "cat-1");
    });
    expect(screen.queryByText("Supermercado")).not.toBeInTheDocument();
  });
});
