import { z } from "zod";

export const categoryFormSchema = z.object({
  name: z.string().trim().min(1, "Indica un nombre para la categoria.").max(120),
  type: z.enum(["income", "expense"]),
  icon: z.string().trim().min(1, "Indica un icono para la categoria.").max(64),
  color: z
    .string()
    .trim()
    .min(1, "Indica un color para la categoria.")
    .max(32)
    .regex(/^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/, "Usa un color hexadecimal valido."),
});

export type CategoryFormValues = z.infer<typeof categoryFormSchema>;
