"use client";

import React from "react";
import { useEffect, useState } from "react";

import {
  CategoryForm,
  DEFAULT_CATEGORY_FORM_VALUES,
} from "@/components/categories/category-form";
import { getErrorMessage } from "@/lib/auth/errors";
import {
  archiveCategory,
  createCategory,
  listCategories,
  updateCategory,
} from "@/lib/categories/api";
import { CATEGORY_TYPE_LABELS, getSelectableCategories } from "@/lib/categories/presentation";
import type { Category, CategoryCreatePayload } from "@/lib/categories/types";

type CategoriesPanelProps = {
  workspaceId: string;
};

type Notice = {
  type: "error" | "success";
  message: string;
};

function toCategoryFormDefaults(category: Category) {
  return {
    name: category.name,
    type: category.type,
    icon: category.icon,
    color: category.color,
  } as const;
}

export function CategoriesPanel({ workspaceId }: CategoriesPanelProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);

  const loadCategories = React.useCallback(async () => {
    setIsLoading(true);

    try {
      const response = await listCategories(workspaceId);
      setCategories(getSelectableCategories(response.categories));
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    setEditingCategoryId(null);
    setNotice(null);

    void loadCategories();
  }, [loadCategories]);

  const handleCreate = async (payload: CategoryCreatePayload) => {
    setNotice(null);

    try {
      const category = await createCategory(workspaceId, payload);
      setCategories((currentCategories) => getSelectableCategories([category, ...currentCategories]));
      setNotice({ type: "success", message: `Categoria ${category.name} creada correctamente.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleUpdate = async (categoryId: string, payload: CategoryCreatePayload) => {
    setNotice(null);

    try {
      const updatedCategory = await updateCategory(workspaceId, categoryId, payload);
      setCategories((currentCategories) =>
        getSelectableCategories(
          currentCategories.map((category) =>
            category.id === updatedCategory.id ? updatedCategory : category,
          ),
        ),
      );
      setNotice({ type: "success", message: `Categoria ${updatedCategory.name} actualizada.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleArchive = async (category: Category) => {
    const shouldArchive = window.confirm(
      `Vas a archivar la categoria ${category.name}. Dejara de aparecer en los selectores activos.`,
    );

    if (!shouldArchive) {
      return;
    }

    setNotice(null);

    try {
      const archivedCategory = await archiveCategory(workspaceId, category.id);
      setCategories((currentCategories) =>
        currentCategories.filter((currentCategory) => currentCategory.id !== archivedCategory.id),
      );
      if (editingCategoryId === archivedCategory.id) {
        setEditingCategoryId(null);
      }
      setNotice({ type: "success", message: `Categoria ${archivedCategory.name} archivada.` });
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  return (
    <section className="workspace-panel">
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Categorias</h2>
        <p className="workspace-section-copy">
          Las listas y selectores muestran categorias activas por defecto para mantener limpio el flujo.
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
          <h3 className="workspace-section-title">Nueva categoria</h3>
          <p className="workspace-section-copy">
            Las categorias base sembradas por backend aparecen aqui y puedes ampliarlas segun el espacio.
          </p>
        </div>
        <CategoryForm
          defaultValues={DEFAULT_CATEGORY_FORM_VALUES}
          fieldIdPrefix={`category-create-${workspaceId}`}
          onSubmitCategory={handleCreate}
          resetOnSuccess
          submitLabel="Crear categoria"
          submittingLabel="Guardando..."
        />
      </div>

      <div className="entity-list" aria-label="Categorias activas del espacio">
        {isLoading ? <p className="workspace-section-copy">Cargando categorias...</p> : null}

        {!isLoading && categories.length === 0 ? (
          <p className="workspace-section-copy">
            Todavia no hay categorias activas. Crea una para clasificar mejor tus movimientos.
          </p>
        ) : null}

        {!isLoading
          ? categories.map((category) => {
              const isEditing = editingCategoryId === category.id;

              return (
                <article key={category.id} className="entity-card">
                  <div className="entity-card-header">
                    <div>
                      <div className="workspace-list-topline">
                        <strong>{category.name}</strong>
                        <span className="workspace-role-chip">{CATEGORY_TYPE_LABELS[category.type]}</span>
                      </div>
                      <p className="workspace-section-copy">
                        Icono <code>{category.icon}</code>
                      </p>
                    </div>
                    <div className="entity-card-side">
                      <span
                        aria-hidden="true"
                        className="entity-color-swatch"
                        style={{ backgroundColor: category.color }}
                      />
                      <span className="workspace-member-date">{category.color}</span>
                    </div>
                  </div>

                  <div className="entity-actions">
                    <button
                      className="secondary-action entity-secondary-action"
                      onClick={() => setEditingCategoryId(isEditing ? null : category.id)}
                      type="button"
                    >
                      {isEditing ? "Cerrar edicion" : "Editar"}
                    </button>
                    <button
                      className="secondary-action entity-danger-action"
                      onClick={() => {
                        void handleArchive(category);
                      }}
                      type="button"
                    >
                      Archivar
                    </button>
                  </div>

                  {isEditing ? (
                    <div className="entity-inline-form">
                      <div className="workspace-form-header">
                        <h3 className="workspace-section-title">Editar categoria</h3>
                        <p className="workspace-section-copy">
                          Ajusta nombre, color o icono sin perder la relacion historica con movimientos.
                        </p>
                      </div>
                      <CategoryForm
                        defaultValues={toCategoryFormDefaults(category)}
                        fieldIdPrefix={`category-edit-${category.id}`}
                        onCancel={() => setEditingCategoryId(null)}
                        onSubmitCategory={(payload) => handleUpdate(category.id, payload)}
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
