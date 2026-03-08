import { z } from "zod";

export const signInSchema = z.object({
  email: z.email("Ingresa un correo electronico valido."),
  password: z.string().min(8, "La contrasena debe tener al menos 8 caracteres."),
});

export const signUpSchema = signInSchema;

export const passwordResetRequestSchema = z.object({
  email: z.email("Ingresa un correo electronico valido."),
});

export const passwordResetConfirmSchema = z.object({
  token: z.string().min(20, "El token debe tener al menos 20 caracteres."),
  newPassword: z.string().min(8, "La contrasena debe tener al menos 8 caracteres."),
});

export type SignInValues = z.infer<typeof signInSchema>;
export type SignUpValues = z.infer<typeof signUpSchema>;
export type PasswordResetRequestValues = z.infer<typeof passwordResetRequestSchema>;
export type PasswordResetConfirmValues = z.infer<typeof passwordResetConfirmSchema>;
