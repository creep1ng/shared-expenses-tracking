import { z } from "zod";

export const categoryFormSchema = z.object({
  name: z.string().trim().min(1, "Indica un nombre para la categoría.").max(120),
  type: z.enum(["income", "expense"]),
  icon: z.string().trim().min(1, "Indica un ícono para la categoría.").max(64),
  color: z
    .string()
    .trim()
    .min(1, "Indica un color para la categoría.")
    .max(32)
    .regex(/^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/, "Usa un color hexadecimal válido."),
});

export type CategoryFormValues = z.infer<typeof categoryFormSchema>;
