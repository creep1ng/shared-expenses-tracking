import { z } from "zod";

export const workspaceCreateSchema = z.object({
  name: z.string().trim().min(1, "Indica un nombre para el espacio.").max(120),
  type: z.enum(["personal", "shared"]),
});

export const workspaceUpdateSchema = z.object({
  name: z.string().trim().min(1, "Indica un nombre para el espacio.").max(120),
});

export const workspaceInvitationSchema = z.object({
  email: z.string().trim().email("Introduce un correo electronico valido."),
});

export const acceptWorkspaceInvitationSchema = z.object({
  token: z.string().trim().min(20, "Introduce un token de invitacion valido."),
});

export type WorkspaceCreateValues = z.infer<typeof workspaceCreateSchema>;
export type WorkspaceUpdateValues = z.infer<typeof workspaceUpdateSchema>;
export type WorkspaceInvitationValues = z.infer<typeof workspaceInvitationSchema>;
export type AcceptWorkspaceInvitationValues = z.infer<typeof acceptWorkspaceInvitationSchema>;
