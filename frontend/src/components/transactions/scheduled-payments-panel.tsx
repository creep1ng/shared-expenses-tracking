"use client";

import React, { useState } from "react";

type ScheduledPayment = {
  id: string;
  description: string;
  amount_minor: number;
  currency: string;
  next_occurrence: string;
  frequency: "daily" | "weekly" | "monthly" | "yearly";
  is_active: boolean;
  category_name?: string;
  days_until_due: number;
};

type ScheduledPaymentsPanelProps = {
  payments: ScheduledPayment[];
};

const FREQUENCY_LABELS: Record<string, string> = {
  daily: "Diario",
  weekly: "Semanal",
  monthly: "Mensual",
  yearly: "Anual",
};

export function ScheduledPaymentsPanel({ payments }: ScheduledPaymentsPanelProps) {
  const activePayments = payments.filter((p) => p.is_active);
  const upcomingPayments = activePayments
    .filter((p) => p.days_until_due <= 7)
    .sort((a, b) => a.days_until_due - b.days_until_due);

  const [showAll, setShowAll] = useState(false);
  const displayPayments = showAll ? activePayments : upcomingPayments;

  const getWarningVariant = (days: number) => {
    if (days <= 1) return "critical";
    if (days <= 3) return "warning";
    return "normal";
  };

  return (
    <section className="workspace-panel">
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Pagos programados</h2>
        <p className="workspace-section-copy">
          Gestiona pagos recurrentes y recibe alertas antes de su vencimiento
        </p>
      </div>

      {upcomingPayments.length > 0 && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <span className="text-xl">⏰</span>
            <div className="flex-1">
              <p className="font-medium text-amber-800">
                Tienes {upcomingPayments.length} pago{upcomingPayments.length > 1 ? "s" : ""} que vence
                {upcomingPayments.length > 1 ? "n" : ""} pronto
              </p>
              <ul className="mt-2 space-y-1">
                {upcomingPayments.slice(0, 3).map((payment) => (
                  <li key={payment.id} className="text-sm text-amber-700">
                    <strong>{payment.description}</strong>: vence en {payment.days_until_due} día
                    {payment.days_until_due !== 1 ? "s" : ""}
                  </li>
                ))}
                {upcomingPayments.length > 3 && (
                  <li className="text-sm text-amber-600">
                    Y {upcomingPayments.length - 3} más...
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button
            className={`text-sm px-3 py-1 rounded ${!showAll ? "bg-slate-100 font-medium" : "text-slate-500"}`}
            onClick={() => setShowAll(false)}
          >
            Próximos
          </button>
          <button
            className={`text-sm px-3 py-1 rounded ${showAll ? "bg-slate-100 font-medium" : "text-slate-500"}`}
            onClick={() => setShowAll(true)}
          >
            Todos
          </button>
        </div>

        <button className="primary-action text-sm px-3 py-1.5">Nuevo pago programado</button>
      </div>

      <div className="entity-list">
        {displayPayments.length === 0 ? (
          <p className="workspace-section-copy py-6 text-center">
            No hay pagos programados {showAll ? "" : "próximos"}.
          </p>
        ) : (
          displayPayments.map((payment) => {
            const variant = getWarningVariant(payment.days_until_due);
            return (
              <article
                key={payment.id}
                className={`entity-card ${variant === "critical" ? "border-l-4 border-l-rose-500" : variant === "warning" ? "border-l-4 border-l-amber-500" : ""}`}
              >
                <div className="entity-card-header">
                  <div>
                    <div className="workspace-list-topline">
                      <strong>{payment.description}</strong>
                      <span className="workspace-role-chip">{FREQUENCY_LABELS[payment.frequency]}</span>
                    </div>
                    <p className="workspace-section-copy">{payment.category_name || "Sin categoría"}</p>
                    <p className="text-xs mt-1">
                      Próximo: {new Date(payment.next_occurrence).toLocaleDateString("es-ES")}
                      {payment.days_until_due === 0 && (
                        <span className="ml-2 text-rose-600 font-medium">¡Hoy!</span>
                      )}
                      {payment.days_until_due === 1 && (
                        <span className="ml-2 text-amber-600 font-medium">Mañana</span>
                      )}
                      {payment.days_until_due > 1 && (
                        <span className="ml-2 text-slate-500">({payment.days_until_due} días)</span>
                      )}
                    </p>
                  </div>
                  <div className="entity-card-side">
                    <span className="account-balance font-medium">
                      ${(payment.amount_minor / 100).toFixed(2)}
                    </span>
                    <span className="workspace-member-date">{payment.currency}</span>
                  </div>
                </div>

                <div className="entity-actions">
                  <button className="secondary-action entity-secondary-action">Ver detalle</button>
                  <button className="secondary-action entity-secondary-action">Editar</button>
                  <button className="secondary-action entity-danger-action">Pausar</button>
                </div>
              </article>
            );
          })
        )}
      </div>
    </section>
  );
}
