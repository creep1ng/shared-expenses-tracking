import React from "react";

import { WORKSPACE_ROLE_LABELS, WORKSPACE_TYPE_LABELS } from "@/lib/workspaces/presentation";
import type { Workspace } from "@/lib/workspaces/types";

type WorkspaceListProps = {
  workspaces: Workspace[];
  selectedWorkspaceId: string | null;
  onSelect: (workspaceId: string) => void;
};

export function WorkspaceList({ workspaces, selectedWorkspaceId, onSelect }: WorkspaceListProps) {
  if (workspaces.length === 0) {
    return (
      <div className="workspace-empty-panel">
        <h2 className="workspace-section-title">Sin espacios todavia</h2>
        <p className="workspace-section-copy">
          Crea tu primer espacio para empezar a gestionar miembros, invitaciones y ajustes.
        </p>
      </div>
    );
  }

  return (
    <div className="workspace-list" aria-label="Espacios de trabajo">
      {workspaces.map((workspace) => {
        const isActive = workspace.id === selectedWorkspaceId;

        return (
          <button
            key={workspace.id}
            className={`workspace-list-item${isActive ? " workspace-list-item-active" : ""}`}
            onClick={() => onSelect(workspace.id)}
            type="button"
          >
            <span className="workspace-list-topline">
              <strong>{workspace.name}</strong>
              <span className="workspace-role-chip">
                {WORKSPACE_ROLE_LABELS[workspace.current_user_role]}
              </span>
            </span>
            <span className="workspace-list-meta">
              {WORKSPACE_TYPE_LABELS[workspace.type]} · {workspace.member_count} integrantes
            </span>
          </button>
        );
      })}
    </div>
  );
}
