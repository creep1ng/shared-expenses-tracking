"use client";

import React from "react";
import { useEffect, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  ACCOUNT_TYPE_OPTIONS,
  buildAccountPayload,
} from "@/lib/accounts/presentation";
import { accountFormSchema, type AccountFormValues } from "@/lib/accounts/schemas";
import type { AccountCreatePayload } from "@/lib/accounts/types";

export const DEFAULT_ACCOUNT_FORM_VALUES: AccountFormValues = {
  name: "",
  type: "bank_account",
  currency: "EUR",
  initialBalance: "0.00",
  description: "",
};

type AccountFormProps = {
  defaultValues?: AccountFormValues;
  submitLabel: string;
  submittingLabel: string;
  onSubmitAccount: (payload: AccountCreatePayload) => Promise<boolean>;
  onCancel?: () => void;
  resetOnSuccess?: boolean;
  fieldIdPrefix: string;
};

export function AccountForm({
  defaultValues = DEFAULT_ACCOUNT_FORM_VALUES,
  submitLabel,
  submittingLabel,
  onSubmitAccount,
  onCancel,
  resetOnSuccess = false,
  fieldIdPrefix,
}: AccountFormProps) {
  const [isPending, startTransition] = useTransition();
  const form = useForm<AccountFormValues>({
    resolver: zodResolver(accountFormSchema),
    defaultValues,
  });

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  const onSubmit = form.handleSubmit((values) => {
    startTransition(async () => {
      const isSuccessful = await onSubmitAccount(buildAccountPayload(values));

      if (!isSuccessful) {
        return;
      }

      if (resetOnSuccess) {
        form.reset(DEFAULT_ACCOUNT_FORM_VALUES);
      }

      onCancel?.();
    });
  });

  return (
    <form className="workspace-form" onSubmit={onSubmit} noValidate>
      <div className="entity-split-grid">
        <label className="auth-field" htmlFor={`${fieldIdPrefix}-name`}>
          <span className="auth-label">Nombre</span>
          <input
            id={`${fieldIdPrefix}-name`}
            className="auth-input"
            type="text"
            placeholder="Ej. Cuenta principal"
            aria-invalid={Boolean(form.formState.errors.name)}
            {...form.register("name")}
          />
          {form.formState.errors.name ? (
            <span className="auth-field-error">{form.formState.errors.name.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-type`}>
          <span className="auth-label">Tipo</span>
          <select
            id={`${fieldIdPrefix}-type`}
            className="auth-input"
            aria-invalid={Boolean(form.formState.errors.type)}
            {...form.register("type")}
          >
            {ACCOUNT_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {form.formState.errors.type ? (
            <span className="auth-field-error">{form.formState.errors.type.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-currency`}>
          <span className="auth-label">Moneda</span>
          <input
            id={`${fieldIdPrefix}-currency`}
            className="auth-input"
            type="text"
            inputMode="text"
            maxLength={3}
            placeholder="EUR"
            aria-invalid={Boolean(form.formState.errors.currency)}
            {...form.register("currency")}
          />
          {form.formState.errors.currency ? (
            <span className="auth-field-error">{form.formState.errors.currency.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-initial-balance`}>
          <span className="auth-label">Saldo inicial</span>
          <input
            id={`${fieldIdPrefix}-initial-balance`}
            className="auth-input"
            type="text"
            inputMode="decimal"
            placeholder="0.00"
            aria-invalid={Boolean(form.formState.errors.initialBalance)}
            {...form.register("initialBalance")}
          />
          {form.formState.errors.initialBalance ? (
            <span className="auth-field-error">{form.formState.errors.initialBalance.message}</span>
          ) : null}
        </label>
      </div>

      <label className="auth-field" htmlFor={`${fieldIdPrefix}-description`}>
        <span className="auth-label">Descripcion</span>
        <textarea
          id={`${fieldIdPrefix}-description`}
          className="auth-input auth-textarea"
          rows={3}
          placeholder="Opcional. Anota detalles para identificar la cuenta."
          aria-invalid={Boolean(form.formState.errors.description)}
          {...form.register("description")}
        />
        {form.formState.errors.description ? (
          <span className="auth-field-error">{form.formState.errors.description.message}</span>
        ) : null}
      </label>

      <div className="entity-actions">
        <button className="primary-action entity-submit" type="submit" disabled={isPending}>
          {isPending ? submittingLabel : submitLabel}
        </button>
        {onCancel ? (
          <button className="secondary-action entity-secondary-action" onClick={onCancel} type="button">
            Cancelar
          </button>
        ) : null}
      </div>
    </form>
  );
}
