"use client";

import React from "react";
import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import { useForm, useWatch, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import type { Account } from "@/lib/accounts/types";
import type { Category } from "@/lib/categories/types";
import type { WorkspaceMember } from "@/lib/workspaces/types";
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
  isSplit: false,
  splits: [],
  tags: [],
  location: "",
};

type TransactionFormProps = {
  accounts: Account[];
  categories: Category[];
  members: WorkspaceMember[];
  defaultValues?: TransactionFormValues;
  submitLabel: string;
  submittingLabel: string;
  onSubmitTransaction: (payload: TransactionCreatePayload, receiptFile?: File | null) => Promise<boolean>;
  onCancel?: () => void;
  resetOnSuccess?: boolean;
  fieldIdPrefix: string;
  allowReceiptUpload?: boolean;
};

export function TransactionForm({
  accounts,
  categories,
  members,
  defaultValues = DEFAULT_TRANSACTION_FORM_VALUES,
  submitLabel,
  submittingLabel,
  onSubmitTransaction,
  onCancel,
  resetOnSuccess = false,
  fieldIdPrefix,
  allowReceiptUpload = false,
}: TransactionFormProps) {
  const [isPending, startTransition] = useTransition();
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const receiptInputRef = useRef<HTMLInputElement | null>(null);
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

  // Construir árbol jerárquico de categorías con indentación
  const hierarchicalCategories = useMemo(() => {
    const buildTree = (parentId: string | null, depth: number = 0): Array<{ category: Category; depth: number }> => {
      const result: Array<{ category: Category; depth: number }> = [];
      const children = selectableCategories.filter(c => c.parent_id === parentId);
      
      children.forEach(child => {
        result.push({ category: child, depth });
        result.push(...buildTree(child.id, depth + 1));
      });
      
      return result;
    };

    return buildTree(null);
  }, [selectableCategories]);

  // Split fields array
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "splits",
  });

  const isSplit = useWatch({ control: form.control, name: "isSplit" });
  const amount = useWatch({ control: form.control, name: "amount" });

  // Calcular suma actual de splits
  const splitsSum = useMemo(() => {
    if (!form.getValues().splits) return 0;
    return form.getValues().splits.reduce((sum, split) => {
      return sum + parseFloat((split.amount || "0").replace(',', '.'));
    }, 0);
  }, [form.watch("splits")]);

  const resolvedCurrency = useMemo(
    () => resolveTransactionCurrency({ type: transactionType, sourceAccountId, destinationAccountId }, accounts),
    [accounts, destinationAccountId, sourceAccountId, transactionType],
  );

  useEffect(() => {
    form.reset(defaultValues);

    setReceiptFile(null);

    if (receiptInputRef.current) {
      receiptInputRef.current.value = "";
    }
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

      const isSuccessful = await onSubmitTransaction(payload, receiptFile);

      if (!isSuccessful) {
        return;
      }

      if (resetOnSuccess) {
        form.reset({
          ...DEFAULT_TRANSACTION_FORM_VALUES,
          occurredAt: getCurrentDateTimeInputValue(),
        });
        setReceiptFile(null);

        if (receiptInputRef.current) {
          receiptInputRef.current.value = "";
        }
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
              {hierarchicalCategories.map(({ category, depth }) => (
                <option key={category.id} value={category.id}>
                  {"\u00A0\u00A0".repeat(depth)}{depth > 0 ? "└ " : ""}{category.name}
                </option>
              ))}
            </select>
            {form.formState.errors.categoryId ? (
              <span className="auth-field-error">{form.formState.errors.categoryId.message}</span>
            ) : null}
          </label>
        ) : null}
      </div>

      {/* Toggle para dividir gasto */}
      {transactionType === "expense" && members.length > 1 ? (
        <div className="auth-field mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              {...form.register("isSplit")}
            />
            <span className="text-sm font-medium">Dividir gasto entre miembros</span>
          </label>
        </div>
      ) : null}

      {/* Campos dinámicos de splits */}
      {isSplit && (
        <div className="mb-6 space-y-3">
          <div className="text-sm text-gray-500 mb-2 flex justify-between">
            <span>Distribución del gasto:</span>
            <span className={Math.abs(parseFloat(amount.replace(',', '.')) - splitsSum) > 0.01 ? "text-red-500 font-semibold" : "text-green-600 font-semibold"}>
              Total: {splitsSum.toFixed(2)} / {amount}
            </span>
          </div>

          {fields.map((field, index) => (
            <div key={field.id} className="flex gap-2 items-center">
              <select
                className="auth-input flex-1"
                {...form.register(`splits.${index}.memberId`)}
              >
                <option value="">Selecciona miembro</option>
                {members.map(member => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.email}
                  </option>
                ))}
              </select>
              <input
                type="text"
                inputMode="decimal"
                className="auth-input w-32"
                placeholder="0.00"
                {...form.register(`splits.${index}.amount`)}
              />
              <button
                type="button"
                onClick={() => remove(index)}
                className="text-red-500 hover:text-red-700 px-2"
              >
                ✕
              </button>
            </div>
          ))}

          <button
            type="button"
            onClick={() => append({ memberId: "", amount: "0.00", percentage: 0 })}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            + Añadir participante
          </button>

          {form.formState.errors.splits ? (
            <span className="auth-field-error">{form.formState.errors.splits.message}</span>
          ) : null}
        </div>
      )}

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

      {allowReceiptUpload ? (
        <label className="auth-field" htmlFor={`${fieldIdPrefix}-receipt`}>
          <span className="auth-label">Adjuntar recibo</span>
          <input
            id={`${fieldIdPrefix}-receipt`}
            ref={receiptInputRef}
            className="auth-input"
            type="file"
            accept="image/*,.pdf"
            onChange={(event) => {
              const nextFile = event.target.files?.[0] ?? null;
              setReceiptFile(nextFile);
            }}
          />
        </label>
      ) : null}

      {/* Acordeón campos avanzados */}
      <details className="mt-4 border rounded-md">
        <summary className="p-3 cursor-pointer text-sm font-medium">
          Opciones avanzadas
        </summary>
        <div className="p-3 space-y-4 border-t">
          <label className="auth-field" htmlFor={`${fieldIdPrefix}-tags`}>
            <span className="auth-label">Etiquetas</span>
            <input
              id={`${fieldIdPrefix}-tags`}
              className="auth-input"
              type="text"
              placeholder="separadas por comas"
              onChange={(e) => form.setValue("tags", e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
            />
          </label>

          <label className="auth-field" htmlFor={`${fieldIdPrefix}-location`}>
            <span className="auth-label">Ubicación</span>
            <input
              id={`${fieldIdPrefix}-location`}
              className="auth-input"
              type="text"
              placeholder="Opcional"
              {...form.register("location")}
            />
          </label>
        </div>
      </details>

      <div className="transaction-form-hint mt-4" aria-live="polite">
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
