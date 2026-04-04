"use client";

import React from "react";
import { useEffect, useState } from "react";

import { AccountsPanel } from "@/components/accounts/accounts-panel";
import { CategoriesPanel } from "@/components/categories/categories-panel";
import { DashboardKpiOverview } from "@/components/dashboard/dashboard-kpi-overview";
import { TransactionsPanel } from "@/components/transactions/transactions-panel";
import { WorkspaceInvitationsPanel } from "@/components/workspaces/workspace-invitations-panel";
import { WorkspaceMembersList } from "@/components/workspaces/workspace-members-list";
import { WorkspaceSummary } from "@/components/workspaces/workspace-summary";
import { TopNav } from "@/components/ui/top-nav";
import { getErrorMessage } from "@/lib/auth/errors";
import type { User } from "@/lib/auth/types";
import {
  createWorkspaceInvitation,
  getWorkspace,
  listWorkspaceInvitations,
  listWorkspaceMembers,
  listWorkspaces,
  revokeWorkspaceInvitation,
  updateWorkspace,
} from "@/lib/workspaces/api";
import type {
  Workspace,
  WorkspaceInvitation,
  WorkspaceMember,
} from "@/lib/workspaces/types";

type WorkspaceDashboardProps = {
  user: User;
  initialWorkspaceId?: string | null;
};

type Notice = {
  type: "error" | "success";
  message: string;
};

function upsertWorkspace(workspaces: Workspace[], nextWorkspace: Workspace): Workspace[] {
  const withoutCurrent = workspaces.filter((workspace) => workspace.id !== nextWorkspace.id);

  return [nextWorkspace, ...withoutCurrent];
}

export function WorkspaceDashboard({ user, initialWorkspaceId = null }: WorkspaceDashboardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingWorkspace, setIsRefreshingWorkspace] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(initialWorkspaceId);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [accountsRefreshNonce, setAccountsRefreshNonce] = useState(0);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [latestInvitationToken, setLatestInvitationToken] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [activeTab, setActiveTab] = useState<"home" | "movimientos" | "cuentas" | "categorias">("home");

  const refreshSelectedWorkspace = React.useCallback(async (workspaceId: string) => {
    setIsRefreshingWorkspace(true);
    setLatestInvitationToken(null);

    try {
      const workspace = await getWorkspace(workspaceId);
      const [membersResponse, invitationsResponse] = await Promise.all([
        listWorkspaceMembers(workspaceId),
        workspace.current_user_role === "owner"
          ? listWorkspaceInvitations(workspaceId)
          : Promise.resolve({ invitations: [] }),
      ]);

      setSelectedWorkspace(workspace);
      setMembers(membersResponse.members);
      setInvitations(invitationsResponse.invitations);
      setWorkspaces((currentWorkspaces) => upsertWorkspace(currentWorkspaces, workspace));
      setSelectedWorkspaceId(workspace.id);
    } finally {
      setIsRefreshingWorkspace(false);
    }
  }, []);

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setIsLoading(true);

      try {
        const response = await listWorkspaces();

        if (!isActive) {
          return;
        }

        setWorkspaces(response.workspaces);

        if (response.workspaces.length === 0) {
          setSelectedWorkspaceId(null);
          setSelectedWorkspace(null);
          setMembers([]);
          setInvitations([]);
          setLatestInvitationToken(null);
          return;
        }

        const preferredWorkspace =
          response.workspaces.find((workspace) => workspace.id === initialWorkspaceId) ||
          response.workspaces[0];

        await refreshSelectedWorkspace(preferredWorkspace.id);
      } catch (error) {
        if (isActive) {
          setNotice({ type: "error", message: getErrorMessage(error) });
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      isActive = false;
    };
  }, [initialWorkspaceId, refreshSelectedWorkspace]);

  const handleSelectWorkspace = async (workspaceId: string) => {
    setNotice(null);

    try {
      await refreshSelectedWorkspace(workspaceId);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  const handleTransactionsChanged = React.useCallback(async () => {
    if (!selectedWorkspace) {
      return;
    }

    setAccountsRefreshNonce((currentNonce) => currentNonce + 1);

    try {
      await refreshSelectedWorkspace(selectedWorkspace.id);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  }, [refreshSelectedWorkspace, selectedWorkspace]);

  const handleRenameWorkspace = async (values: { name: string }) => {
    if (!selectedWorkspaceId) {
      return false;
    }

    setNotice(null);

    try {
      const workspace = await updateWorkspace(selectedWorkspaceId, values);
      setSelectedWorkspace(workspace);
      setWorkspaces((currentWorkspaces) => upsertWorkspace(currentWorkspaces, workspace));
      setNotice({ type: "success", message: "Nombre del espacio actualizado." });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleCreateInvitation = async (values: { email: string }) => {
    if (!selectedWorkspaceId) {
      return false;
    }

    setNotice(null);

    try {
      const invitation = await createWorkspaceInvitation(selectedWorkspaceId, values);
      setInvitations((currentInvitations) => [invitation, ...currentInvitations]);
      setLatestInvitationToken(invitation.invitation_token);
      setNotice({ type: "success", message: `Invitacion creada para ${invitation.invited_email}.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleRevokeInvitation = async (invitationId: string) => {
    if (!selectedWorkspaceId) {
      return false;
    }

    setNotice(null);

    try {
      const revokedInvitation = await revokeWorkspaceInvitation(selectedWorkspaceId, invitationId);
      setInvitations((currentInvitations) =>
        currentInvitations.map((invitation) =>
          invitation.id === revokedInvitation.id ? revokedInvitation : invitation,
        ),
      );
      setNotice({ type: "success", message: `Invitacion revocada para ${revokedInvitation.invited_email}.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  return (
    <>
      <TopNav 
        user={user} 
        workspaces={workspaces} 
        selectedWorkspaceId={selectedWorkspaceId} 
        onSelectWorkspace={handleSelectWorkspace} 
        activeTab={activeTab} 
        onTabChange={(tab) => setActiveTab(tab as "home" | "movimientos" | "cuentas" | "categorias")} 
      />
      <main className="main-content">
        {notice ? (
          <div
            className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
            role={notice.type === "error" ? "alert" : "status"}
            style={{ marginBottom: '2rem' }}
          >
            {notice.message}
          </div>
        ) : null}

        {isLoading ? <div className="workspace-panel">Cargando espacios...</div> : null}

        {!isLoading && !selectedWorkspace ? (
          <section className="workspace-panel workspace-empty-state">
            <h2 className="workspace-section-title">Tu panel esta listo</h2>
            <p className="workspace-section-copy">
              Crea un espacio desde la opción superior o acepta una invitacion existente para ver
              datos compartidos.
            </p>
          </section>
        ) : null}

        {selectedWorkspace ? (
          <div className="workspace-main-column" style={{ maxWidth: '100%' }}>
            {isRefreshingWorkspace ? <div className="workspace-loading-bar">Actualizando datos...</div> : null}
            
            {activeTab === "home" && (
              <div className="home-grid">
                <div className="home-column">
                  <WorkspaceSummary workspace={selectedWorkspace} onRename={handleRenameWorkspace} />
                  <WorkspaceMembersList members={members} />
                  <WorkspaceInvitationsPanel
                    workspace={selectedWorkspace}
                    invitations={invitations}
                    latestInvitationToken={latestInvitationToken}
                    onCreateInvitation={handleCreateInvitation}
                    onRevokeInvitation={handleRevokeInvitation}
                  />
                  <TransactionsPanel
                    workspaceId={selectedWorkspace.id}
                    mode="recent"
                    onTransactionsChanged={handleTransactionsChanged}
                  />
                </div>
                <div className="home-column">
                  <DashboardKpiOverview workspaceId={selectedWorkspace.id} refreshNonce={accountsRefreshNonce} />
                  <AccountsPanel workspaceId={selectedWorkspace.id} refreshNonce={accountsRefreshNonce} mode="readonly" />
                </div>
              </div>
            )}

            {activeTab === "movimientos" && (
              <TransactionsPanel
                workspaceId={selectedWorkspace.id}
                mode="crud"
                onTransactionsChanged={() => {
                  void handleTransactionsChanged();
                }}
              />
            )}

            {activeTab === "cuentas" && (
              <AccountsPanel workspaceId={selectedWorkspace.id} refreshNonce={accountsRefreshNonce} mode="crud" />
            )}

            {activeTab === "categorias" && (
              <CategoriesPanel workspaceId={selectedWorkspace.id} mode="crud" />
            )}
          </div>
        ) : null}
      </main>
    </>
  );
}
