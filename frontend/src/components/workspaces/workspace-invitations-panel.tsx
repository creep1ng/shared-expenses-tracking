"use client";

import React from "react";
import { useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  INVITATION_STATUS_LABELS,
  WORKSPACE_ROLE_LABELS,
  formatDateTime,
} from "@/lib/workspaces/presentation";
import {
  workspaceInvitationSchema,
  type WorkspaceInvitationValues,
} from "@/lib/workspaces/schemas";
import type { Workspace, WorkspaceInvitation } from "@/lib/workspaces/types";

type WorkspaceInvitationsPanelProps = {
  workspace: Workspace;
  invitations: WorkspaceInvitation[];
  latestInvitationToken: string | null;
  onCreateInvitation: (values: WorkspaceInvitationValues) => Promise<boolean>;
  onRevokeInvitation: (invitationId: string) => Promise<boolean>;
};

export function WorkspaceInvitationsPanel({
  workspace,
  invitations,
  latestInvitationToken,
  onCreateInvitation,
  onRevokeInvitation,
}: WorkspaceInvitationsPanelProps) {
  const isOwner = workspace.current_user_role === "owner";
  const [isCreating, startCreating] = useTransition();
  const [revokingId, setRevokingId] = React.useState<string | null>(null);
  const form = useForm<WorkspaceInvitationValues>({
    resolver: zodResolver(workspaceInvitationSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    startCreating(async () => {
      const isSuccessful = await onCreateInvitation(values);

      if (isSuccessful) {
        form.reset();
      }
    });
  });

  if (!isOwner) {
    return (
      <section className="workspace-panel">
        <div className="workspace-form-header">
          <h2 className="workspace-section-title">Invitaciones</h2>
          <p className="workspace-section-copy">
            Tu rol actual es {WORKSPACE_ROLE_LABELS[workspace.current_user_role].toLowerCase()}. Solo la
            persona propietaria puede invitar o revocar accesos.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="workspace-panel">
      <form className="workspace-form workspace-inline-form" onSubmit={onSubmit} noValidate>
        <div className="workspace-form-header">
          <h2 className="workspace-section-title">Invitaciones</h2>
          <p className="workspace-section-copy">
            Invita por correo y comparte el token devuelto mientras el flujo de email aun no exista.
          </p>
        </div>

        <label className="auth-field" htmlFor="invitation-email">
          <span className="auth-label">Correo a invitar</span>
          <input
            id="invitation-email"
            className="auth-input"
            type="email"
            placeholder="persona@ejemplo.com"
            aria-invalid={Boolean(form.formState.errors.email)}
            {...form.register("email")}
          />
          {form.formState.errors.email ? (
            <span className="auth-field-error">{form.formState.errors.email.message}</span>
          ) : null}
        </label>

        <button className="secondary-action workspace-inline-submit" type="submit" disabled={isCreating}>
          {isCreating ? "Enviando..." : "Crear invitacion"}
        </button>
      </form>

      {latestInvitationToken ? (
        <div className="auth-feedback auth-feedback-success" role="status">
          Token de invitacion generado: <code>{latestInvitationToken}</code>
        </div>
      ) : null}

      <div className="workspace-invitation-list" aria-label="Invitaciones del espacio">
        {invitations.length === 0 ? (
          <p className="workspace-section-copy">Todavia no hay invitaciones registradas para este espacio.</p>
        ) : null}

        {invitations.map((invitation) => {
          const canRevoke = invitation.status === "pending";

          return (
            <article key={invitation.id} className="workspace-invitation-card">
              <div>
                <strong>{invitation.invited_email}</strong>
                <p>
                  {INVITATION_STATUS_LABELS[invitation.status]} · Expira {formatDateTime(invitation.expires_at)}
                </p>
              </div>
              <div className="workspace-invitation-actions">
                <span className="workspace-member-date">Creada {formatDateTime(invitation.created_at)}</span>
                {canRevoke ? (
                  <button
                    className="workspace-link-button"
                    onClick={() => {
                      setRevokingId(invitation.id);
                      void onRevokeInvitation(invitation.id).finally(() => setRevokingId(null));
                    }}
                    type="button"
                    disabled={revokingId === invitation.id}
                  >
                    {revokingId === invitation.id ? "Revocando..." : "Revocar"}
                  </button>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
