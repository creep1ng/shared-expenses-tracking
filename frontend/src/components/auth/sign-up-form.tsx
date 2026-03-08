"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { Route } from "next";

import { AuthCard } from "@/components/auth/auth-card";
import { AuthErrorBanner } from "@/components/auth/auth-error-banner";
import { signIn, signUp } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import { signUpSchema, type SignUpValues } from "@/lib/auth/schemas";

export function SignUpForm() {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const form = useForm<SignUpValues>({
    resolver: zodResolver(signUpSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    setSubmitError(null);

    startTransition(async () => {
      try {
        await signUp(values);
        await signIn(values);
        router.replace("/" as Route);
        router.refresh();
      } catch (error) {
        setSubmitError(getErrorMessage(error));
      }
    });
  });

  return (
    <AuthCard
      eyebrow="Crear cuenta"
      title="Abre tu acceso"
      description="Crea una cuenta para comenzar a registrar gastos personales o compartidos."
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
            autoComplete="new-password"
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
          {isPending ? "Creando cuenta..." : "Crear cuenta"}
        </button>

        <div className="auth-links-row">
          <Link href={"/sign-in" as Route}>Ya tengo cuenta</Link>
        </div>
      </form>
    </AuthCard>
  );
}
