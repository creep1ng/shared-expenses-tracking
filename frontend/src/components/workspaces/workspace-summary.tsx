"use client";

import React from "react";
import { useEffect, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  WORKSPACE_ROLE_LABELS,
  WORKSPACE_TYPE_LABELS,
  formatDateTime,
} from "@/lib/workspaces/presentation";
import { workspaceUpdateSchema, type WorkspaceUpdateValues } from "@/lib/workspaces/schemas";
import type { Workspace } from "@/lib/workspaces/types";

type WorkspaceSummaryProps = {
  workspace: Workspace;
  onRename: (values: WorkspaceUpdateValues) => Promise<boolean>;
};

export function WorkspaceSummary({ workspace, onRename }: WorkspaceSummaryProps) {
  const isOwner = workspace.current_user_role === "owner";
  const [isPending, startTransition] = useTransition();
  const form = useForm<WorkspaceUpdateValues>({
    resolver: zodResolver(workspaceUpdateSchema),
    defaultValues: {
      name: workspace.name,
    },
  });

  useEffect(() => {
    form.reset({ name: workspace.name });
  }, [form, workspace.name]);

  const onSubmit = form.handleSubmit((values) => {
    startTransition(async () => {
      await onRename(values);
    });
  });

  return (
    <section className="workspace-panel workspace-summary-panel">
      <div className="workspace-summary-header">
        <div>
          <span className="dashboard-eyebrow">Espacio activo</span>
          <h1 className="workspace-headline">{workspace.name}</h1>
          <p className="dashboard-copy">
            Este tablero usa la sesion actual del backend y refleja el rol real devuelto por la API.
          </p>
        </div>
      </div>

      <div className="workspace-stat-grid" aria-label="Resumen del espacio">
        <article className="dashboard-stat">
          <span className="dashboard-stat-label">Tipo</span>
          <span className="dashboard-stat-value">{WORKSPACE_TYPE_LABELS[workspace.type]}</span>
        </article>
        <article className="dashboard-stat">
          <span className="dashboard-stat-label">Tu rol</span>
          <span className="dashboard-stat-value">{WORKSPACE_ROLE_LABELS[workspace.current_user_role]}</span>
        </article>
        <article className="dashboard-stat">
          <span className="dashboard-stat-label">Integrantes</span>
          <span className="dashboard-stat-value">{workspace.member_count}</span>
        </article>
      </div>

      <dl className="workspace-facts">
        <div>
          <dt>Creado</dt>
          <dd>{formatDateTime(workspace.created_at)}</dd>
        </div>
        <div>
          <dt>Actualizado</dt>
          <dd>{formatDateTime(workspace.updated_at)}</dd>
        </div>
      </dl>

      {isOwner ? (
        <form className="workspace-form workspace-inline-form" onSubmit={onSubmit} noValidate>
          <div className="workspace-form-header">
            <h2 className="workspace-section-title">Ajustes basicos</h2>
            <p className="workspace-section-copy">
              Como persona propietaria, puedes renombrar el espacio y gestionar invitaciones.
            </p>
          </div>

          <label className="auth-field" htmlFor="workspace-rename">
            <span className="auth-label">Nombre del espacio</span>
            <input
              id="workspace-rename"
              className="auth-input"
              type="text"
              aria-invalid={Boolean(form.formState.errors.name)}
              {...form.register("name")}
            />
            {form.formState.errors.name ? (
              <span className="auth-field-error">{form.formState.errors.name.message}</span>
            ) : null}
          </label>

          <button className="secondary-action workspace-inline-submit" type="submit" disabled={isPending}>
            {isPending ? "Guardando..." : "Guardar nombre"}
          </button>
        </form>
      ) : (
        <div className="workspace-note">
          Tu acceso es de miembro. La API mantiene el control de permisos para cambios sensibles.
        </div>
      )}
    </section>
  );
}
