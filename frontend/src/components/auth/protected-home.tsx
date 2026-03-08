"use client";

import React from "react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { signOut } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import type { User } from "@/lib/auth/types";

type ProtectedHomeProps = {
  user: User;
};

export function ProtectedHome({ user }: ProtectedHomeProps) {
  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleSignOut = () => {
    setErrorMessage(null);

    startTransition(async () => {
      try {
        await signOut();
        router.replace("/sign-in" as Route);
        router.refresh();
      } catch (error) {
        setErrorMessage(getErrorMessage(error));
      }
    });
  };

  return (
    <main className="dashboard-shell">
      <section className="dashboard-card">
        <span className="dashboard-eyebrow">Sesion activa</span>
        <h1 className="dashboard-title">Bienvenida a tu espacio de gastos compartidos.</h1>
        <p className="dashboard-copy">
          Has iniciado sesion como <strong>{user.email}</strong>. Esta pantalla confirma que la
          ruta principal esta protegida por la sesion del backend.
        </p>

        <div className="dashboard-stats" aria-label="Resumen de autenticacion">
          <article className="dashboard-stat">
            <span className="dashboard-stat-label">Estado</span>
            <span className="dashboard-stat-value">Autenticada</span>
          </article>
          <article className="dashboard-stat">
            <span className="dashboard-stat-label">Origen</span>
            <span className="dashboard-stat-value">/api/v1/auth/me</span>
          </article>
          <article className="dashboard-stat">
            <span className="dashboard-stat-label">Sesion</span>
            <span className="dashboard-stat-value">Cookie segura</span>
          </article>
        </div>

        {errorMessage ? (
          <div className="auth-feedback auth-feedback-error" role="alert">
            {errorMessage}
          </div>
        ) : null}

        <div className="dashboard-actions">
          <button className="primary-action" onClick={handleSignOut} type="button" disabled={isPending}>
            {isPending ? "Cerrando sesion..." : "Cerrar sesion"}
          </button>
          <a className="secondary-action" href="/password-reset/request">
            Solicitar recuperacion de contrasena
          </a>
        </div>
      </section>
    </main>
  );
}
