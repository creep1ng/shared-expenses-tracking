import React from "react";

import { WORKSPACE_ROLE_LABELS, formatDateTime } from "@/lib/workspaces/presentation";
import type { WorkspaceMember } from "@/lib/workspaces/types";

type WorkspaceMembersListProps = {
  members: WorkspaceMember[];
};

export function WorkspaceMembersList({ members }: WorkspaceMembersListProps) {
  return (
    <section className="workspace-panel">
      <div className="workspace-form-header">
        <h2 className="workspace-section-title">Integrantes</h2>
        <p className="workspace-section-copy">
          Lista actual de personas con acceso al espacio seleccionado.
        </p>
      </div>

      <div className="workspace-member-list" aria-label="Integrantes del espacio">
        {members.map((member) => (
          <article key={member.user_id} className="workspace-member-card">
            <div>
              <strong>{member.email}</strong>
              <p>
                {WORKSPACE_ROLE_LABELS[member.role]} · {member.is_active ? "Activa" : "Inactiva"}
              </p>
            </div>
            <span className="workspace-member-date">Desde {formatDateTime(member.joined_at)}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
