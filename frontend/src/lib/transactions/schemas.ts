import { z } from "zod";

const splitItemSchema = z.object({
  memberId: z.string().min(1, "Selecciona un miembro"),
  amount: z.string().min(1, "Indica el importe"),
  percentage: z.number().min(0).max(100).optional(),
});

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
    isSplit: z.boolean(),
    splits: z.array(splitItemSchema).optional(),
    tags: z.array(z.string()).optional(),
    location: z.string().optional(),
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

    // Validación de splits
    if (values.isSplit && values.splits && values.splits.length > 0) {
      const totalAmount = parseFloat(values.amount.replace(',', '.'));
      const splitsSum = values.splits.reduce((sum, split) => {
        return sum + parseFloat(split.amount.replace(',', '.'));
      }, 0);

      if (Math.abs(totalAmount - splitsSum) > 0.01) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: `La suma de los splits (${splitsSum.toFixed(2)}) no coincide con el monto total (${totalAmount.toFixed(2)}).`,
          path: ["splits"],
        });
      }
    }
  });

export type TransactionFormValues = z.infer<typeof transactionFormSchema>;
