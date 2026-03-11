"use client";

import React from "react";
import { useEffect, useMemo, useTransition } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import type { Account } from "@/lib/accounts/types";
import type { Category } from "@/lib/categories/types";
import { transactionFormSchema, type TransactionFormValues } from "@/lib/transactions/schemas";
import {
  buildTransactionPayload,
  getCurrentDateTimeInputValue,
  getMaxDateTimeInputValue,
  getSelectableTransactionCategories,
  resolveTransactionCurrency,
  TRANSACTION_TYPE_LABELS,
  TRANSACTION_TYPE_OPTIONS,
} from "@/lib/transactions/presentation";
import type { TransactionCreatePayload } from "@/lib/transactions/types";

export const DEFAULT_TRANSACTION_FORM_VALUES: TransactionFormValues = {
  type: "expense",
  sourceAccountId: "",
  destinationAccountId: "",
  categoryId: "",
  amount: "0.00",
  occurredAt: getCurrentDateTimeInputValue(),
  description: "",
};

type TransactionFormProps = {
  accounts: Account[];
  categories: Category[];
  defaultValues?: TransactionFormValues;
  submitLabel: string;
  submittingLabel: string;
  onSubmitTransaction: (payload: TransactionCreatePayload) => Promise<boolean>;
  onCancel?: () => void;
  resetOnSuccess?: boolean;
  fieldIdPrefix: string;
};

export function TransactionForm({
  accounts,
  categories,
  defaultValues = DEFAULT_TRANSACTION_FORM_VALUES,
  submitLabel,
  submittingLabel,
  onSubmitTransaction,
  onCancel,
  resetOnSuccess = false,
  fieldIdPrefix,
}: TransactionFormProps) {
  const [isPending, startTransition] = useTransition();
  const form = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionFormSchema),
    defaultValues,
  });

  const transactionType = useWatch({ control: form.control, name: "type" });
  const sourceAccountId = useWatch({ control: form.control, name: "sourceAccountId" });
  const destinationAccountId = useWatch({ control: form.control, name: "destinationAccountId" });
  const categoryId = useWatch({ control: form.control, name: "categoryId" });

  const selectableCategories = useMemo(
    () => getSelectableTransactionCategories(categories, transactionType),
    [categories, transactionType],
  );

  const resolvedCurrency = useMemo(
    () => resolveTransactionCurrency({ type: transactionType, sourceAccountId, destinationAccountId }, accounts),
    [accounts, destinationAccountId, sourceAccountId, transactionType],
  );

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  useEffect(() => {
    if (transactionType === "transfer" && categoryId) {
      form.setValue("categoryId", "", { shouldDirty: true, shouldValidate: true });
      return;
    }

    if (categoryId && !selectableCategories.some((category) => category.id === categoryId)) {
      form.setValue("categoryId", "", { shouldDirty: true, shouldValidate: true });
    }
  }, [categoryId, form, selectableCategories, transactionType]);

  const onSubmit = form.handleSubmit((values) => {
    startTransition(async () => {
      let payload: TransactionCreatePayload;

      try {
        payload = buildTransactionPayload(values, accounts);
      } catch (error) {
        form.setError("root", { message: error instanceof Error ? error.message : "No se pudo preparar el movimiento." });
        return;
      }

      const isSuccessful = await onSubmitTransaction(payload);

      if (!isSuccessful) {
        return;
      }

      if (resetOnSuccess) {
        form.reset({
          ...DEFAULT_TRANSACTION_FORM_VALUES,
          occurredAt: getCurrentDateTimeInputValue(),
        });
      }

      onCancel?.();
    });
  });

  return (
    <form className="workspace-form" onSubmit={onSubmit} noValidate>
      <div className="entity-split-grid">
        <label className="auth-field" htmlFor={`${fieldIdPrefix}-type`}>
          <span className="auth-label">Tipo de movimiento</span>
          <select
            id={`${fieldIdPrefix}-type`}
            className="auth-input"
            aria-invalid={Boolean(form.formState.errors.type)}
            {...form.register("type")}
          >
            {TRANSACTION_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {form.formState.errors.type ? (
            <span className="auth-field-error">{form.formState.errors.type.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-amount`}>
          <span className="auth-label">Importe</span>
          <input
            id={`${fieldIdPrefix}-amount`}
            className="auth-input"
            type="text"
            inputMode="decimal"
            placeholder="0.00"
            aria-invalid={Boolean(form.formState.errors.amount)}
            {...form.register("amount")}
          />
          {form.formState.errors.amount ? (
            <span className="auth-field-error">{form.formState.errors.amount.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-occurred-at`}>
          <span className="auth-label">Fecha y hora</span>
          <input
            id={`${fieldIdPrefix}-occurred-at`}
            className="auth-input"
            type="datetime-local"
            max={getMaxDateTimeInputValue()}
            aria-invalid={Boolean(form.formState.errors.occurredAt)}
            {...form.register("occurredAt")}
          />
          {form.formState.errors.occurredAt ? (
            <span className="auth-field-error">{form.formState.errors.occurredAt.message}</span>
          ) : null}
        </label>

        {transactionType !== "income" ? (
          <label className="auth-field" htmlFor={`${fieldIdPrefix}-source-account`}>
            <span className="auth-label">Cuenta de origen</span>
            <select
              id={`${fieldIdPrefix}-source-account`}
              className="auth-input"
              aria-invalid={Boolean(form.formState.errors.sourceAccountId)}
              {...form.register("sourceAccountId")}
            >
              <option value="">Selecciona una cuenta</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.currency})
                </option>
              ))}
            </select>
            {form.formState.errors.sourceAccountId ? (
              <span className="auth-field-error">{form.formState.errors.sourceAccountId.message}</span>
            ) : null}
          </label>
        ) : null}

        {transactionType !== "expense" ? (
          <label className="auth-field" htmlFor={`${fieldIdPrefix}-destination-account`}>
            <span className="auth-label">Cuenta de destino</span>
            <select
              id={`${fieldIdPrefix}-destination-account`}
              className="auth-input"
              aria-invalid={Boolean(form.formState.errors.destinationAccountId)}
              {...form.register("destinationAccountId")}
            >
              <option value="">Selecciona una cuenta</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.currency})
                </option>
              ))}
            </select>
            {form.formState.errors.destinationAccountId ? (
              <span className="auth-field-error">{form.formState.errors.destinationAccountId.message}</span>
            ) : null}
          </label>
        ) : null}

        {transactionType !== "transfer" ? (
          <label className="auth-field" htmlFor={`${fieldIdPrefix}-category`}>
            <span className="auth-label">Categoria</span>
            <select
              id={`${fieldIdPrefix}-category`}
              className="auth-input"
              aria-invalid={Boolean(form.formState.errors.categoryId)}
              {...form.register("categoryId")}
            >
              <option value="">Selecciona una categoria</option>
              {selectableCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {form.formState.errors.categoryId ? (
              <span className="auth-field-error">{form.formState.errors.categoryId.message}</span>
            ) : null}
          </label>
        ) : null}
      </div>

      <label className="auth-field" htmlFor={`${fieldIdPrefix}-description`}>
        <span className="auth-label">Descripcion</span>
        <textarea
          id={`${fieldIdPrefix}-description`}
          className="auth-input auth-textarea"
          rows={3}
          placeholder={
            transactionType === "transfer"
              ? "Opcional. Ej. Traspaso a la cuenta de ahorro."
              : "Opcional. Anota un detalle para identificar el movimiento."
          }
          aria-invalid={Boolean(form.formState.errors.description)}
          {...form.register("description")}
        />
        {form.formState.errors.description ? (
          <span className="auth-field-error">{form.formState.errors.description.message}</span>
        ) : null}
      </label>

      <div className="transaction-form-hint" aria-live="polite">
        <strong>{TRANSACTION_TYPE_LABELS[transactionType]}</strong>
        <span>
          {transactionType === "transfer"
            ? resolvedCurrency
              ? ` Se registrara en ${resolvedCurrency} y no pedira categoria.`
              : " Selecciona dos cuentas con la misma moneda para registrar la transferencia."
            : resolvedCurrency
              ? ` Se registrara en ${resolvedCurrency}.`
              : " La moneda se toma de la cuenta seleccionada."}
        </span>
      </div>

      {form.formState.errors.root?.message ? (
        <div className="auth-feedback auth-feedback-error" role="alert">
          {form.formState.errors.root.message}
        </div>
      ) : null}

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
