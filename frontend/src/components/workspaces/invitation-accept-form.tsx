"use client";

import React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { getErrorMessage } from "@/lib/auth/errors";
import {
  acceptWorkspaceInvitationSchema,
  type AcceptWorkspaceInvitationValues,
} from "@/lib/workspaces/schemas";
import { acceptWorkspaceInvitation } from "@/lib/workspaces/api";

export function InvitationAcceptForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const form = useForm<AcceptWorkspaceInvitationValues>({
    resolver: zodResolver(acceptWorkspaceInvitationSchema),
    defaultValues: {
      token: "",
    },
  });

  useEffect(() => {
    const token = searchParams.get("token");

    if (token) {
      form.setValue("token", token);
    }
  }, [form, searchParams]);

  const onSubmit = form.handleSubmit((values) => {
    setSubmitError(null);
    setSuccessMessage(null);

    startTransition(async () => {
      try {
        const response = await acceptWorkspaceInvitation({ token: values.token });
        setSuccessMessage(`Te has unido a ${response.workspace.name}.`);
        window.setTimeout(() => {
          router.replace(`/?workspace=${response.workspace.id}`);
          router.refresh();
        }, 900);
      } catch (error) {
        setSubmitError(getErrorMessage(error));
      }
    });
  });

  return (
    <AuthCard
      eyebrow="Invitacion"
      title="Aceptar invitacion"
      description="Usa el token emitido por la API para unirte a un espacio compartido existente."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <AuthErrorBanner message={submitError} />

        {successMessage ? (
          <div className="auth-feedback auth-feedback-success" role="status">
            {successMessage}
          </div>
        ) : null}

        <label className="auth-field" htmlFor="invitation-token">
          <span className="auth-label">Token de invitacion</span>
          <input
            id="invitation-token"
            className="auth-input"
            type="text"
            aria-invalid={Boolean(form.formState.errors.token)}
            {...form.register("token")}
          />
          {form.formState.errors.token ? (
            <span className="auth-field-error">{form.formState.errors.token.message}</span>
          ) : null}
        </label>

        <button className="primary-action auth-submit" type="submit" disabled={isPending}>
          {isPending ? "Aceptando..." : "Aceptar invitacion"}
        </button>

        <div className="auth-links-row">
          <Link href="/">Volver al tablero</Link>
        </div>
      </form>
    </AuthCard>
  );
}
