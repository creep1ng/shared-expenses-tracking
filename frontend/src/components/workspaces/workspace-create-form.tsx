"use client";

import React from "react";
import { useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { workspaceCreateSchema, type WorkspaceCreateValues } from "@/lib/workspaces/schemas";

type WorkspaceCreateFormProps = {
  onCreate: (values: WorkspaceCreateValues) => Promise<boolean>;
};

export function WorkspaceCreateForm({ onCreate }: WorkspaceCreateFormProps) {
  const [isPending, startTransition] = useTransition();
  const form = useForm<WorkspaceCreateValues>({
    resolver: zodResolver(workspaceCreateSchema),
    defaultValues: {
      name: "",
      type: "personal",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    startTransition(async () => {
      const isSuccessful = await onCreate(values);

      if (isSuccessful) {
        form.reset({
          name: "",
          type: values.type,
        });
      }
    });
  });

  return (
    <form className="workspace-form" onSubmit={onSubmit} noValidate>
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Crear espacio</h2>
        <p className="workspace-section-copy">
          Crea un espacio personal o compartido para empezar a organizar movimientos.
        </p>
      </div>

      <label className="auth-field" htmlFor="workspace-name">
        <span className="auth-label">Nombre</span>
        <input
          id="workspace-name"
          className="auth-input"
          type="text"
          placeholder="Ej. Casa con Ana"
          aria-invalid={Boolean(form.formState.errors.name)}
          {...form.register("name")}
        />
        {form.formState.errors.name ? (
          <span className="auth-field-error">{form.formState.errors.name.message}</span>
        ) : null}
      </label>

      <fieldset className="workspace-choice-group">
        <legend className="auth-label">Tipo</legend>
        <label className="workspace-choice">
          <input type="radio" value="personal" {...form.register("type")} />
          <span>
            <strong>Personal</strong>
            <small>Un espacio para tus finanzas individuales.</small>
          </span>
        </label>
        <label className="workspace-choice">
          <input type="radio" value="shared" {...form.register("type")} />
          <span>
            <strong>Compartido</strong>
            <small>Ideal para pareja, casa o viajes.</small>
          </span>
        </label>
      </fieldset>

      <button className="primary-action workspace-submit" type="submit" disabled={isPending}>
        {isPending ? "Creando..." : "Crear espacio"}
      </button>
    </form>
  );
}
