"use client";

import React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { Route } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { signIn } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import { signInSchema, type SignInValues } from "@/lib/auth/schemas";

export function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = (searchParams.get("redirect") || "/") as Route;
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const form = useForm<SignInValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    setSubmitError(null);

    startTransition(async () => {
      try {
        await signIn(values);
        router.replace(redirectTo);
        router.refresh();
      } catch (error) {
        setSubmitError(getErrorMessage(error));
      }
    });
  });

  return (
    <AuthCard
      eyebrow="Iniciar sesion"
      title="Accede a tu cuenta"
      description="Usa tu correo y contrasena para entrar a tu espacio de trabajo."
    >
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <AuthErrorBanner message={submitError} />

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

        <label className="auth-field" htmlFor="password">
          <span className="auth-label">Contrasena</span>
          <input
            autoComplete="current-password"
            className="auth-input"
            id="password"
            type="password"
            aria-invalid={Boolean(form.formState.errors.password)}
            {...form.register("password")}
          />
          {form.formState.errors.password ? (
            <span className="auth-field-error">{form.formState.errors.password.message}</span>
          ) : null}
        </label>

        <button className="primary-action auth-submit" type="submit" disabled={isPending}>
          {isPending ? "Ingresando..." : "Entrar"}
        </button>

        <div className="auth-links-row">
          <Link href={"/sign-up" as Route}>Crear cuenta</Link>
          <Link href={"/password-reset/request" as Route}>Olvide mi contrasena</Link>
        </div>
      </form>
    </AuthCard>
  );
}
