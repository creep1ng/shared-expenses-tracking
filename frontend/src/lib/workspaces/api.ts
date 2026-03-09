import { requestJson } from "@/lib/api/client";
import type {
  AcceptWorkspaceInvitationPayload,
  AcceptWorkspaceInvitationResponse,
  Workspace,
  WorkspaceCreatePayload,
  WorkspaceInvitation,
  WorkspaceInvitationCreatePayload,
  WorkspaceInvitationCreateResponse,
  WorkspaceInvitationsResponse,
  WorkspaceListResponse,
  WorkspaceMembersResponse,
  WorkspaceUpdatePayload,
} from "@/lib/workspaces/types";

export function listWorkspaces(): Promise<WorkspaceListResponse> {
  return requestJson<WorkspaceListResponse>("/workspaces", {
    method: "GET",
  });
}

export function createWorkspace(payload: WorkspaceCreatePayload): Promise<Workspace> {
  return requestJson<Workspace>("/workspaces", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getWorkspace(workspaceId: string): Promise<Workspace> {
  return requestJson<Workspace>(`/workspaces/${workspaceId}`, {
    method: "GET",
  });
}

export function updateWorkspace(workspaceId: string, payload: WorkspaceUpdatePayload): Promise<Workspace> {
  return requestJson<Workspace>(`/workspaces/${workspaceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listWorkspaceMembers(workspaceId: string): Promise<WorkspaceMembersResponse> {
  return requestJson<WorkspaceMembersResponse>(`/workspaces/${workspaceId}/members`, {
    method: "GET",
  });
}

export function createWorkspaceInvitation(
  workspaceId: string,
  payload: WorkspaceInvitationCreatePayload,
): Promise<WorkspaceInvitationCreateResponse> {
  return requestJson<WorkspaceInvitationCreateResponse>(`/workspaces/${workspaceId}/invitations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listWorkspaceInvitations(workspaceId: string): Promise<WorkspaceInvitationsResponse> {
  return requestJson<WorkspaceInvitationsResponse>(`/workspaces/${workspaceId}/invitations`, {
    method: "GET",
  });
}

export function revokeWorkspaceInvitation(
  workspaceId: string,
  invitationId: string,
): Promise<WorkspaceInvitation> {
  return requestJson<WorkspaceInvitation>(
    `/workspaces/${workspaceId}/invitations/${invitationId}/revoke`,
    {
      method: "POST",
    },
  );
}

export function acceptWorkspaceInvitation(
  payload: AcceptWorkspaceInvitationPayload,
): Promise<AcceptWorkspaceInvitationResponse> {
  return requestJson<AcceptWorkspaceInvitationResponse>("/workspaces/invitations/accept", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
