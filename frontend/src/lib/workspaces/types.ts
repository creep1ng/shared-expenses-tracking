export type WorkspaceType = "personal" | "shared";

export type WorkspaceMemberRole = "owner" | "member";

export type WorkspaceInvitationStatus = "pending" | "accepted" | "revoked" | "expired";

export type Workspace = {
  id: string;
  name: string;
  type: WorkspaceType;
  created_by_user_id: string;
  current_user_role: WorkspaceMemberRole;
  member_count: number;
  created_at: string;
  updated_at: string;
};

export type WorkspaceListResponse = {
  workspaces: Workspace[];
};

export type WorkspaceCreatePayload = {
  name: string;
  type: WorkspaceType;
};

export type WorkspaceUpdatePayload = {
  name: string;
};

export type WorkspaceMember = {
  user_id: string;
  email: string;
  is_active: boolean;
  role: WorkspaceMemberRole;
  joined_at: string;
};

export type WorkspaceMembersResponse = {
  members: WorkspaceMember[];
};

export type WorkspaceInvitation = {
  id: string;
  workspace_id: string;
  invited_email: string;
  invited_by_user_id: string;
  accepted_by_user_id: string | null;
  status: WorkspaceInvitationStatus;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkspaceInvitationCreatePayload = {
  email: string;
};

export type WorkspaceInvitationCreateResponse = WorkspaceInvitation & {
  invitation_token: string;
};

export type WorkspaceInvitationsResponse = {
  invitations: WorkspaceInvitation[];
};

export type AcceptWorkspaceInvitationPayload = {
  token: string;
};

export type AcceptWorkspaceInvitationResponse = {
  workspace: Workspace;
};
