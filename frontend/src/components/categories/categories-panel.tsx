"use client";

import React from "react";
import { useEffect, useState } from "react";

import { Modal } from "@/components/ui/modal";
import { Plus } from "lucide-react";
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
  mode?: "crud" | "readonly";
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

export function CategoriesPanel({ workspaceId, mode = "crud" }: CategoriesPanelProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
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
      setIsCreateModalOpen(false);
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
      {mode === "crud" ? (
        <div className="workspace-form-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="workspace-section-title">Categorías</h2>
            <p className="workspace-section-copy">
              Las listas y selectores muestran categorias activas por defecto para mantener limpio el flujo.
            </p>
          </div>
          <button className="primary-action" onClick={() => setIsCreateModalOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Plus size={16} /> Nueva categoría
          </button>
        </div>
      ) : (
        <div className="workspace-form-header">
          <h2 className="workspace-section-title">Categorías</h2>
        </div>
      )}

      {notice ? (
        <div
          className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
          role={notice.type === "error" ? "alert" : "status"}
        >
          {notice.message}
        </div>
      ) : null}

      <div className={mode === "crud" ? "dashboard-kpi-grid" : "dashboard-kpi-grid"} aria-label="Categorias activas del espacio" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
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
                <article key={category.id} className="kpi-card" style={{ borderTop: `4px solid ${category.color}`, padding: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ fontSize: '1.5rem' }}>{category.icon}</span>
                      <h3 className="kpi-label" style={{ fontSize: '1.1rem', margin: 0, color: 'var(--foreground)' }}>{category.name}</h3>
                    </div>
                    <span className="workspace-role-chip" style={{ fontSize: '0.75rem' }}>{CATEGORY_TYPE_LABELS[category.type]}</span>
                  </div>

                  {mode === "crud" && (
                    <div className="entity-actions" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--surface-border)' }}>
                      <button
                        className="secondary-action entity-secondary-action"
                        onClick={() => setEditingCategoryId(isEditing ? null : category.id)}
                        type="button"
                        style={{ flex: 1, padding: '0.4rem' }}
                      >
                        {isEditing ? "Cerrar edicion" : "Editar"}
                      </button>
                      <button
                        className="secondary-action entity-danger-action"
                        onClick={() => {
                          void handleArchive(category);
                        }}
                        type="button"
                        style={{ padding: '0.4rem' }}
                      >
                        Archivar
                      </button>
                    </div>
                  )}

                  {isEditing && mode === "crud" ? (
                    <div className="entity-inline-form" style={{ marginTop: '1rem' }}>
                      <CategoryForm
                        defaultValues={toCategoryFormDefaults(category)}
                        fieldIdPrefix={`category-edit-${category.id}`}
                        onCancel={() => setEditingCategoryId(null)}
                        onSubmitCategory={(payload) => handleUpdate(category.id, payload)}
                        submitLabel="Guardar"
                        submittingLabel="..."
                      />
                    </div>
                  ) : null}
                </article>
              );
            })
          : null}
      </div>

      {mode === "crud" && (
        <Modal 
          isOpen={isCreateModalOpen} 
          onClose={() => setIsCreateModalOpen(false)} 
          title="Nueva categoría"
          description="Las categorias base sembradas por backend aparecen aqui y puedes ampliarlas segun el espacio."
        >
          <CategoryForm
            defaultValues={DEFAULT_CATEGORY_FORM_VALUES}
            fieldIdPrefix={`category-create-${workspaceId}`}
            onSubmitCategory={handleCreate}
            resetOnSuccess
            submitLabel="Crear categoria"
            submittingLabel="Guardando..."
          />
        </Modal>
      )}
    </section>
  );
}
