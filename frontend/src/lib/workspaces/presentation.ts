import type {
  WorkspaceInvitationStatus,
  WorkspaceMemberRole,
  WorkspaceType,
} from "@/lib/workspaces/types";

const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("es-ES", {
  dateStyle: "medium",
  timeStyle: "short",
});

export const WORKSPACE_TYPE_LABELS: Record<WorkspaceType, string> = {
  personal: "Personal",
  shared: "Compartido",
};

export const WORKSPACE_ROLE_LABELS: Record<WorkspaceMemberRole, string> = {
  owner: "Propietario/a",
  member: "Miembro",
};

export const INVITATION_STATUS_LABELS: Record<WorkspaceInvitationStatus, string> = {
  pending: "Pendiente",
  accepted: "Aceptada",
  revoked: "Revocada",
  expired: "Expirada",
};

export function formatDateTime(value: string): string {
  return DATE_TIME_FORMATTER.format(new Date(value));
}
