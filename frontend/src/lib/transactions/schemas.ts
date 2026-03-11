import { z } from "zod";

export const transactionFormSchema = z
  .object({
    type: z.enum(["income", "expense", "transfer"]),
    sourceAccountId: z.string().trim().optional(),
    destinationAccountId: z.string().trim().optional(),
    categoryId: z.string().trim().optional(),
    amount: z
      .string()
      .trim()
      .min(1, "Indica el importe del movimiento.")
      .regex(/^\d+(?:[.,]\d{1,2})?$/, "Introduce un importe valido con hasta 2 decimales."),
    occurredAt: z.string().trim().min(1, "Indica la fecha y hora del movimiento."),
    description: z.string().trim().max(1000, "La descripcion no puede superar 1000 caracteres.").optional(),
  })
  .superRefine((values, context) => {
    const sourceAccountId = values.sourceAccountId?.trim() ?? "";
    const destinationAccountId = values.destinationAccountId?.trim() ?? "";
    const categoryId = values.categoryId?.trim() ?? "";

    if (Number.isNaN(new Date(values.occurredAt).getTime())) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Indica una fecha y hora validas.",
        path: ["occurredAt"],
      });
      return;
    }

    const occurredDate = new Date(values.occurredAt);
    const today = new Date();
    today.setHours(23, 59, 59, 999);

    if (occurredDate > today) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "La fecha no puede ser posterior a hoy.",
        path: ["occurredAt"],
      });
    }

    if (values.type === "income") {
      if (!destinationAccountId) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Selecciona la cuenta de destino.",
          path: ["destinationAccountId"],
        });
      }

      if (!categoryId) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Selecciona una categoria de ingreso.",
          path: ["categoryId"],
        });
      }

      return;
    }

    if (values.type === "expense") {
      if (!sourceAccountId) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Selecciona la cuenta de origen.",
          path: ["sourceAccountId"],
        });
      }

      if (!categoryId) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Selecciona una categoria de gasto.",
          path: ["categoryId"],
        });
      }

      return;
    }

    if (!sourceAccountId) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Selecciona la cuenta de origen.",
        path: ["sourceAccountId"],
      });
    }

    if (!destinationAccountId) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Selecciona la cuenta de destino.",
        path: ["destinationAccountId"],
      });
    }

    if (sourceAccountId && destinationAccountId && sourceAccountId === destinationAccountId) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "La transferencia debe usar cuentas distintas.",
        path: ["destinationAccountId"],
      });
    }
  });

export type TransactionFormValues = z.infer<typeof transactionFormSchema>;
