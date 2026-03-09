"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";

import { AccountsPanel } from "@/components/accounts/accounts-panel";
import { CategoriesPanel } from "@/components/categories/categories-panel";
import { WorkspaceCreateForm } from "@/components/workspaces/workspace-create-form";
import { WorkspaceInvitationsPanel } from "@/components/workspaces/workspace-invitations-panel";
import { WorkspaceList } from "@/components/workspaces/workspace-list";
import { WorkspaceMembersList } from "@/components/workspaces/workspace-members-list";
import { WorkspaceSummary } from "@/components/workspaces/workspace-summary";
import { signOut } from "@/lib/auth/api";
import { getErrorMessage } from "@/lib/auth/errors";
import type { User } from "@/lib/auth/types";
import {
  createWorkspace,
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
  const router = useRouter();
  const [isSigningOut, startSignOutTransition] = useTransition();
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingWorkspace, setIsRefreshingWorkspace] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(initialWorkspaceId);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [latestInvitationToken, setLatestInvitationToken] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);

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

  const handleSignOut = () => {
    setNotice(null);

    startSignOutTransition(async () => {
      try {
        await signOut();
        router.replace("/sign-in");
        router.refresh();
      } catch (error) {
        setNotice({ type: "error", message: getErrorMessage(error) });
      }
    });
  };

  const handleSelectWorkspace = async (workspaceId: string) => {
    setNotice(null);

    try {
      await refreshSelectedWorkspace(workspaceId);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    }
  };

  const handleCreateWorkspace = async (values: { name: string; type: "personal" | "shared" }) => {
    setNotice(null);

    try {
      const workspace = await createWorkspace(values);
      setWorkspaces((currentWorkspaces) => upsertWorkspace(currentWorkspaces, workspace));
      await refreshSelectedWorkspace(workspace.id);
      setNotice({ type: "success", message: `Espacio ${workspace.name} creado correctamente.` });
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

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
    <main className="workspace-dashboard-shell">
      <section className="workspace-dashboard-card">
        <header className="workspace-dashboard-header">
          <div>
            <span className="dashboard-eyebrow">Sesion activa</span>
            <h1 className="dashboard-title">Tablero de espacios de trabajo</h1>
            <p className="dashboard-copy">
              Has iniciado sesion como <strong>{user.email}</strong>. Desde aqui puedes crear espacios,
              revisar miembros y gestionar invitaciones segun tu rol.
            </p>
          </div>

          <div className="dashboard-actions">
            <Link className="secondary-action" href="/invitations/accept">
              Aceptar invitacion
            </Link>
            <button className="primary-action" onClick={handleSignOut} type="button" disabled={isSigningOut}>
              {isSigningOut ? "Cerrando sesion..." : "Cerrar sesion"}
            </button>
          </div>
        </header>

        {notice ? (
          <div
            className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
            role={notice.type === "error" ? "alert" : "status"}
          >
            {notice.message}
          </div>
        ) : null}

        <div className="workspace-dashboard-grid">
          <aside className="workspace-sidebar">
            <WorkspaceCreateForm onCreate={handleCreateWorkspace} />
            <section className="workspace-panel">
              <div className="workspace-form-header">
                <h2 className="workspace-section-title">Tus espacios</h2>
                <p className="workspace-section-copy">
                  Elige un espacio para consultar sus detalles y permisos disponibles.
                </p>
              </div>
              <WorkspaceList
                workspaces={workspaces}
                selectedWorkspaceId={selectedWorkspaceId}
                onSelect={(workspaceId) => {
                  void handleSelectWorkspace(workspaceId);
                }}
              />
            </section>
          </aside>

          <div className="workspace-main-column">
            {isLoading ? <div className="workspace-panel">Cargando espacios...</div> : null}

            {!isLoading && !selectedWorkspace ? (
              <section className="workspace-panel workspace-empty-state">
                <h2 className="workspace-section-title">Tu panel esta listo</h2>
                <p className="workspace-section-copy">
                  Crea un espacio desde la columna lateral o acepta una invitacion existente para ver
                  datos compartidos.
                </p>
              </section>
            ) : null}

            {selectedWorkspace ? (
              <>
                {isRefreshingWorkspace ? <div className="workspace-loading-bar">Actualizando datos...</div> : null}
                <WorkspaceSummary workspace={selectedWorkspace} onRename={handleRenameWorkspace} />
                <AccountsPanel workspaceId={selectedWorkspace.id} />
                <CategoriesPanel workspaceId={selectedWorkspace.id} />
                <WorkspaceMembersList members={members} />
                <WorkspaceInvitationsPanel
                  workspace={selectedWorkspace}
                  invitations={invitations}
                  latestInvitationToken={latestInvitationToken}
                  onCreateInvitation={handleCreateInvitation}
                  onRevokeInvitation={handleRevokeInvitation}
                />
              </>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
