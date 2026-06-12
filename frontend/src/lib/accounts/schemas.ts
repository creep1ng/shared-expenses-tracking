import { z } from "zod";

export const accountFormSchema = z.object({
  name: z.string().trim().min(1, "Indica un nombre para la cuenta.").max(120),
  type: z.enum(["cash", "bank_account", "savings_account", "credit_card"]),
  currency: z
    .string()
    .trim()
    .min(3, "Usa un código ISO de 3 letras.")
    .max(3, "Usa un código ISO de 3 letras.")
    .regex(/^[a-zA-Z]{3}$/, "Usa un código ISO de 3 letras."),
  initialBalance: z
    .string()
    .trim()
    .min(1, "Indica el saldo inicial.")
    .regex(/^-?\d+(?:[.,]\d{1,2})?$/, "Introduce un importe válido con hasta 2 decimales."),
  description: z.string().trim().max(1000, "La descripción no puede superar 1000 caracteres.").optional(),
});

export type AccountFormValues = z.infer<typeof accountFormSchema>;
