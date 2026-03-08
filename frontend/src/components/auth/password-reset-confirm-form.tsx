"use client";

import React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { Route } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { confirmPasswordReset } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import {
  passwordResetConfirmSchema,
  type PasswordResetConfirmValues,
} from "@/lib/auth/schemas";

export function PasswordResetConfirmForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const form = useForm<PasswordResetConfirmValues>({
    resolver: zodResolver(passwordResetConfirmSchema),
    defaultValues: {
      token: "",
      newPassword: "",
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
        const response = await confirmPasswordReset({
          token: values.token,
          new_password: values.newPassword,
        });
        setSuccessMessage(response.message);
        window.setTimeout(() => {
          router.replace("/sign-in" as Route);
          router.refresh();
        }, 1200);
      } catch (error) {
        setSubmitError(getErrorMessage(error));
      }
    });
  });

  return (
    <AuthCard
      eyebrow="Actualizar contrasena"
      title="Confirma tu nueva contrasena"
      description="Pega el token emitido por el backend y define una nueva contrasena segura."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <AuthErrorBanner message={submitError} />

        {successMessage ? (
          <div className="auth-feedback auth-feedback-success" role="status">
            {successMessage}
          </div>
        ) : null}

        <label className="auth-field" htmlFor="token">
          <span className="auth-label">Token de recuperacion</span>
          <input
            autoComplete="one-time-code"
            className="auth-input"
            id="token"
            type="text"
            aria-invalid={Boolean(form.formState.errors.token)}
            {...form.register("token")}
          />
          {form.formState.errors.token ? (
            <span className="auth-field-error">{form.formState.errors.token.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor="newPassword">
          <span className="auth-label">Nueva contrasena</span>
          <input
            autoComplete="new-password"
            className="auth-input"
            id="newPassword"
            type="password"
            aria-invalid={Boolean(form.formState.errors.newPassword)}
            {...form.register("newPassword")}
          />
          {form.formState.errors.newPassword ? (
            <span className="auth-field-error">{form.formState.errors.newPassword.message}</span>
          ) : null}
        </label>

        <button className="primary-action auth-submit" type="submit" disabled={isPending}>
          {isPending ? "Actualizando..." : "Actualizar contrasena"}
        </button>

        <div className="auth-links-row">
          <Link href={"/sign-in" as Route}>Volver a iniciar sesion</Link>
        </div>
      </form>
    </AuthCard>
  );
}
