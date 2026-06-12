"use client";

import React from "react";
import { useEffect, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { CATEGORY_TYPE_OPTIONS } from "@/lib/categories/presentation";
import { CategoryIcon, CATEGORY_ICON_OPTIONS } from "@/lib/categories/icons";
import { categoryFormSchema, type CategoryFormValues } from "@/lib/categories/schemas";
import type { CategoryCreatePayload } from "@/lib/categories/types";

export const DEFAULT_CATEGORY_FORM_VALUES: CategoryFormValues = {
  name: "",
  type: "expense",
  icon: "receipt-text",
  color: "#D97706",
};

const CATEGORY_COLOR_OPTIONS = [
  "#D97706",
  "#EA580C",
  "#DC2626",
  "#E11D48",
  "#DB2777",
  "#C026D3",
  "#9333EA",
  "#7C3AED",
  "#4F46E5",
  "#2563EB",
  "#0284C7",
  "#0891B2",
  "#0D9488",
  "#059669",
  "#16A34A",
  "#65A30D",
  "#84CC16",
  "#CA8A04",
  "#A16207",
  "#92400E",
  "#78716C",
  "#52525B",
  "#374151",
  "#111827",
] as const;

function getColorOptions(currentColor: string): string[] {
  const normalizedColor = currentColor.trim().toUpperCase();

  if (!normalizedColor || CATEGORY_COLOR_OPTIONS.includes(normalizedColor as (typeof CATEGORY_COLOR_OPTIONS)[number])) {
    return [...CATEGORY_COLOR_OPTIONS];
  }

  return [normalizedColor, ...CATEGORY_COLOR_OPTIONS];
}

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
  const [iconSearch, setIconSearch] = React.useState("");
  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(categoryFormSchema),
    defaultValues,
  });
  const selectedIcon = form.watch("icon");
  const selectedColor = form.watch("color");
  const colorOptions = getColorOptions(selectedColor || defaultValues.color);

  const visibleIconOptions = CATEGORY_ICON_OPTIONS.filter((option) => {
    const normalizedSearch = iconSearch.trim().toLocaleLowerCase("es");

    if (!normalizedSearch) {
      return true;
    }

    return [option.label, option.slug, ...option.keywords]
      .join(" ")
      .toLocaleLowerCase("es")
      .includes(normalizedSearch);
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
    <form className="workspace-form category-form" onSubmit={onSubmit} noValidate>
      <div className="category-form-grid">
        <label className="auth-field" htmlFor={`${fieldIdPrefix}-name`}>
          <span className="auth-label">Nombre</span>
          <input
            id={`${fieldIdPrefix}-name`}
            className="auth-input"
            type="text"
            placeholder="Ej. Alimentación"
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

        <fieldset className="auth-field category-picker-field category-icon-picker">
          <legend className="auth-label" id={`${fieldIdPrefix}-icon-label`}>
            Ícono
          </legend>
          <input id={`${fieldIdPrefix}-icon`} type="hidden" {...form.register("icon")} />
          <label className="category-icon-search" htmlFor={`${fieldIdPrefix}-icon-search`}>
            <span className="sr-only">Buscar ícono</span>
            <input
              id={`${fieldIdPrefix}-icon-search`}
              className="auth-input"
              type="search"
              placeholder="Buscar ícono"
              value={iconSearch}
              onChange={(event) => setIconSearch(event.target.value)}
            />
          </label>
          <div
            className="category-icon-grid"
            role="radiogroup"
            aria-labelledby={`${fieldIdPrefix}-icon-label`}
            aria-invalid={Boolean(form.formState.errors.icon)}
          >
            {visibleIconOptions.length > 0 ? (
              visibleIconOptions.map((option) => {
                const isSelected = selectedIcon === option.slug;

                return (
                  <button
                    key={option.slug}
                    className={`category-icon-option${isSelected ? " category-icon-option-selected" : ""}`}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    aria-label={option.label}
                    title={option.label}
                    onClick={() => {
                      form.setValue("icon", option.slug, { shouldDirty: true, shouldValidate: true });
                    }}
                  >
                    <CategoryIcon icon={option.slug} size={20} />
                    <span>{option.label}</span>
                  </button>
                );
              })
            ) : (
              <p className="category-icon-empty">No encontramos íconos para esa búsqueda.</p>
            )}
          </div>
          {form.formState.errors.icon ? (
            <span className="auth-field-error">{form.formState.errors.icon.message}</span>
          ) : null}
        </fieldset>

        <fieldset className="auth-field category-picker-field category-color-picker">
          <legend className="auth-label" id={`${fieldIdPrefix}-color-label`}>
            Color
          </legend>
          <input id={`${fieldIdPrefix}-color`} type="hidden" {...form.register("color")} />
          <div
            className="category-color-grid"
            role="radiogroup"
            aria-labelledby={`${fieldIdPrefix}-color-label`}
            aria-invalid={Boolean(form.formState.errors.color)}
          >
            {colorOptions.map((color) => {
              const normalizedColor = color.toUpperCase();
              const isSelected = selectedColor.toUpperCase() === normalizedColor;

              return (
                <button
                  key={normalizedColor}
                  className={`category-color-option${isSelected ? " category-color-option-selected" : ""}`}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  aria-label={`Color ${normalizedColor}`}
                  title={normalizedColor}
                  onClick={() => {
                    form.setValue("color", normalizedColor, { shouldDirty: true, shouldValidate: true });
                  }}
                >
                  <span aria-hidden="true" style={{ backgroundColor: normalizedColor }} />
                </button>
              );
            })}
          </div>
          {form.formState.errors.color ? (
            <span className="auth-field-error">{form.formState.errors.color.message}</span>
          ) : null}
        </fieldset>
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
