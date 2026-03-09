import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspaceDashboard } from "@/components/workspaces/workspace-dashboard";

const replaceMock = vi.fn();
const refreshMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock,
    refresh: refreshMock,
  }),
}));

const signOutMock = vi.fn();

vi.mock("@/lib/auth/api", () => ({
  signOut: (...args: unknown[]) => signOutMock(...args),
}));

const createWorkspaceMock = vi.fn();
const createWorkspaceInvitationMock = vi.fn();
const getWorkspaceMock = vi.fn();
const listWorkspaceInvitationsMock = vi.fn();
const listWorkspaceMembersMock = vi.fn();
const listWorkspacesMock = vi.fn();
const revokeWorkspaceInvitationMock = vi.fn();
const updateWorkspaceMock = vi.fn();

vi.mock("@/lib/workspaces/api", () => ({
  createWorkspace: (...args: unknown[]) => createWorkspaceMock(...args),
  createWorkspaceInvitation: (...args: unknown[]) => createWorkspaceInvitationMock(...args),
  getWorkspace: (...args: unknown[]) => getWorkspaceMock(...args),
  listWorkspaceInvitations: (...args: unknown[]) => listWorkspaceInvitationsMock(...args),
  listWorkspaceMembers: (...args: unknown[]) => listWorkspaceMembersMock(...args),
  listWorkspaces: (...args: unknown[]) => listWorkspacesMock(...args),
  revokeWorkspaceInvitation: (...args: unknown[]) => revokeWorkspaceInvitationMock(...args),
  updateWorkspace: (...args: unknown[]) => updateWorkspaceMock(...args),
}));

const ownerWorkspace = {
  id: "workspace-1",
  name: "Casa",
  type: "shared" as const,
  created_by_user_id: "user-1",
  current_user_role: "owner" as const,
  member_count: 2,
  created_at: "2026-03-08T10:00:00Z",
  updated_at: "2026-03-08T11:00:00Z",
};

const memberWorkspace = {
  ...ownerWorkspace,
  id: "workspace-2",
  name: "Viaje",
  current_user_role: "member" as const,
};

describe("WorkspaceDashboard", () => {
  beforeEach(() => {
    replaceMock.mockReset();
    refreshMock.mockReset();
    signOutMock.mockReset();
    createWorkspaceMock.mockReset();
    createWorkspaceInvitationMock.mockReset();
    getWorkspaceMock.mockReset();
    listWorkspaceInvitationsMock.mockReset();
    listWorkspaceMembersMock.mockReset();
    listWorkspacesMock.mockReset();
    revokeWorkspaceInvitationMock.mockReset();
    updateWorkspaceMock.mockReset();
  });

  it("loads the selected workspace with owner actions", async () => {
    listWorkspacesMock.mockResolvedValue({ workspaces: [ownerWorkspace] });
    getWorkspaceMock.mockResolvedValue(ownerWorkspace);
    listWorkspaceMembersMock.mockResolvedValue({
      members: [
        {
          user_id: "user-1",
          email: "owner@example.com",
          is_active: true,
          role: "owner",
          joined_at: "2026-03-08T10:00:00Z",
        },
      ],
    });
    listWorkspaceInvitationsMock.mockResolvedValue({
      invitations: [
        {
          id: "inv-1",
          workspace_id: "workspace-1",
          invited_email: "ana@example.com",
          invited_by_user_id: "user-1",
          accepted_by_user_id: null,
          status: "pending",
          expires_at: "2026-03-10T10:00:00Z",
          accepted_at: null,
          revoked_at: null,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        },
      ],
    });

    render(
      <WorkspaceDashboard
        user={{
          id: "user-1",
          email: "owner@example.com",
          is_active: true,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        }}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Casa" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar nombre/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /crear invitacion/i })).toBeInTheDocument();
    expect(screen.getAllByText("owner@example.com")).toHaveLength(2);
    expect(screen.getByText("ana@example.com")).toBeInTheDocument();
  });

  it("hides owner-only invitation controls for members", async () => {
    listWorkspacesMock.mockResolvedValue({ workspaces: [memberWorkspace] });
    getWorkspaceMock.mockResolvedValue(memberWorkspace);
    listWorkspaceMembersMock.mockResolvedValue({
      members: [
        {
          user_id: "user-2",
          email: "member@example.com",
          is_active: true,
          role: "member",
          joined_at: "2026-03-08T10:00:00Z",
        },
      ],
    });

    render(
      <WorkspaceDashboard
        user={{
          id: "user-2",
          email: "member@example.com",
          is_active: true,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        }}
      />,
    );

    expect(await screen.findByRole("heading", { name: "Viaje" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /crear invitacion/i })).not.toBeInTheDocument();
    expect(screen.getByText(/solo la persona propietaria puede invitar o revocar accesos/i)).toBeInTheDocument();
    expect(listWorkspaceInvitationsMock).not.toHaveBeenCalled();
  });

  it("creates invitations and exposes the returned token", async () => {
    const user = userEvent.setup();

    listWorkspacesMock.mockResolvedValue({ workspaces: [ownerWorkspace] });
    getWorkspaceMock.mockResolvedValue(ownerWorkspace);
    listWorkspaceMembersMock.mockResolvedValue({ members: [] });
    listWorkspaceInvitationsMock.mockResolvedValue({ invitations: [] });
    createWorkspaceInvitationMock.mockResolvedValue({
      id: "inv-2",
      workspace_id: "workspace-1",
      invited_email: "nueva@example.com",
      invited_by_user_id: "user-1",
      accepted_by_user_id: null,
      status: "pending",
      expires_at: "2026-03-10T10:00:00Z",
      accepted_at: null,
      revoked_at: null,
      created_at: "2026-03-08T10:00:00Z",
      updated_at: "2026-03-08T10:00:00Z",
      invitation_token: "token-demo-12345678901234567890",
    });

    render(
      <WorkspaceDashboard
        user={{
          id: "user-1",
          email: "owner@example.com",
          is_active: true,
          created_at: "2026-03-08T10:00:00Z",
          updated_at: "2026-03-08T10:00:00Z",
        }}
      />,
    );

    await screen.findByRole("heading", { name: "Casa" });

    await user.type(screen.getByLabelText(/correo a invitar/i), "nueva@example.com");
    await user.click(screen.getByRole("button", { name: /crear invitacion/i }));

    await waitFor(() => {
      expect(createWorkspaceInvitationMock).toHaveBeenCalledWith("workspace-1", {
        email: "nueva@example.com",
      });
    });

    expect(await screen.findByText(/token de invitacion generado/i)).toHaveTextContent(
      "token-demo-12345678901234567890",
    );
    expect(screen.getByText("nueva@example.com")).toBeInTheDocument();
  });
});
