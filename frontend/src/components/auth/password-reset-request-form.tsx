"use client";

import React from "react";
import Link from "next/link";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { Route } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { requestPasswordReset } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import {
  passwordResetRequestSchema,
  type PasswordResetRequestValues,
} from "@/lib/auth/schemas";

export function PasswordResetRequestForm() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const form = useForm<PasswordResetRequestValues>({
    resolver: zodResolver(passwordResetRequestSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    setSubmitError(null);
    setSuccessMessage(null);
    setResetToken(null);

    startTransition(async () => {
      try {
        const response = await requestPasswordReset(values);
        setSuccessMessage(response.message);
        setResetToken(response.reset_token);
      } catch (error) {
        setSubmitError(getErrorMessage(error));
      }
    });
  });

  return (
    <AuthCard
      eyebrow="Recuperar acceso"
      title="Solicita el reinicio de contrasena"
      description="Ingresa tu correo y el backend emitira un token de recuperacion si la cuenta existe."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <AuthErrorBanner message={submitError} />

        {successMessage ? (
          <div className="auth-feedback auth-feedback-success" role="status">
            <p>{successMessage}</p>
            {resetToken ? (
              <p>
                Token de desarrollo: <code>{resetToken}</code>
              </p>
            ) : null}
          </div>
        ) : null}

        <label className="auth-field" htmlFor="email">
          <span className="auth-label">Correo electronico</span>
          <input
            autoComplete="email"
            className="auth-input"
            id="email"
            type="email"
            aria-invalid={Boolean(form.formState.errors.email)}
            {...form.register("email")}
          />
          {form.formState.errors.email ? (
            <span className="auth-field-error">{form.formState.errors.email.message}</span>
          ) : null}
        </label>

        <button className="primary-action auth-submit" type="submit" disabled={isPending}>
          {isPending ? "Solicitando..." : "Enviar solicitud"}
        </button>

        <div className="auth-links-row">
          <Link href={"/sign-in" as Route}>Volver a iniciar sesion</Link>
          <Link href={"/password-reset/confirm" as Route}>Ya tengo un token</Link>
        </div>
      </form>
    </AuthCard>
  );
}
