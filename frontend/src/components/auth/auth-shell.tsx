import React from "react";
import type { ReactNode } from "react";

type AuthShellProps = {
  children: ReactNode;
};

export function AuthShell({ children }: AuthShellProps) {
  return (
    <main className="auth-page-shell">
      <div className="auth-page-grid">
        <section className="auth-panel auth-panel-copy">
          <span className="auth-kicker">Shared Expenses</span>
          <h2 className="auth-panel-title">Control de acceso simple, seguro y en espanol.</h2>
          <p className="auth-panel-copy-text">
            La autenticacion depende del backend y de sesiones por cookie HTTP only. El frontend
            consume el estado real de la sesion sin guardar tokens en localStorage.
          </p>
          <div className="auth-panel-points" aria-label="Principios de autenticacion">
            <article>
              <strong>Sesion persistente</strong>
              <p>La sesion se mantiene tras refrescar mientras la cookie siga vigente.</p>
            </article>
            <article>
              <strong>Backend como fuente de verdad</strong>
              <p>La UI valida acceso consultando `/api/v1/auth/me` en lugar de duplicar estado.</p>
            </article>
            <article>
              <strong>Errores claros</strong>
              <p>Los formularios muestran validaciones locales y mensajes devueltos por la API.</p>
            </article>
          </div>
        </section>
        {children}
      </div>
    </main>
  );
}
