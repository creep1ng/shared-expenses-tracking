"use client";

import React from "react";
import { useEffect, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { CATEGORY_TYPE_OPTIONS } from "@/lib/categories/presentation";
import { categoryFormSchema, type CategoryFormValues } from "@/lib/categories/schemas";
import type { CategoryCreatePayload } from "@/lib/categories/types";

export const DEFAULT_CATEGORY_FORM_VALUES: CategoryFormValues = {
  name: "",
  type: "expense",
  icon: "receipt-text",
  color: "#D97706",
};

type CategoryFormProps = {
  defaultValues?: CategoryFormValues;
  submitLabel: string;
  submittingLabel: string;
  onSubmitCategory: (payload: CategoryCreatePayload) => Promise<boolean>;
  onCancel?: () => void;
  resetOnSuccess?: boolean;
  fieldIdPrefix: string;
};

export function CategoryForm({
  defaultValues = DEFAULT_CATEGORY_FORM_VALUES,
  submitLabel,
  submittingLabel,
  onSubmitCategory,
  onCancel,
  resetOnSuccess = false,
  fieldIdPrefix,
}: CategoryFormProps) {
  const [isPending, startTransition] = useTransition();
  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(categoryFormSchema),
    defaultValues,
  });

  useEffect(() => {
    form.reset(defaultValues);
  }, [defaultValues, form]);

  const onSubmit = form.handleSubmit((values) => {
    startTransition(async () => {
      const isSuccessful = await onSubmitCategory({
        name: values.name.trim(),
        type: values.type,
        icon: values.icon.trim(),
        color: values.color.trim().toUpperCase(),
      });

      if (!isSuccessful) {
        return;
      }

      if (resetOnSuccess) {
        form.reset(DEFAULT_CATEGORY_FORM_VALUES);
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
            placeholder="Ej. Alimentacion"
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
            {CATEGORY_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {form.formState.errors.type ? (
            <span className="auth-field-error">{form.formState.errors.type.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-icon`}>
          <span className="auth-label">Icono</span>
          <input
            id={`${fieldIdPrefix}-icon`}
            className="auth-input"
            type="text"
            placeholder="receipt-text"
            aria-invalid={Boolean(form.formState.errors.icon)}
            {...form.register("icon")}
          />
          {form.formState.errors.icon ? (
            <span className="auth-field-error">{form.formState.errors.icon.message}</span>
          ) : null}
        </label>

        <label className="auth-field" htmlFor={`${fieldIdPrefix}-color`}>
          <span className="auth-label">Color</span>
          <input
            id={`${fieldIdPrefix}-color`}
            className="auth-input"
            type="text"
            placeholder="#D97706"
            aria-invalid={Boolean(form.formState.errors.color)}
            {...form.register("color")}
          />
          {form.formState.errors.color ? (
            <span className="auth-field-error">{form.formState.errors.color.message}</span>
          ) : null}
        </label>
      </div>

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
