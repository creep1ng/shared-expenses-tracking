"use client";

import React from "react";

import { WorkspaceDashboard } from "@/components/workspaces/workspace-dashboard";
import type { User } from "@/lib/auth/types";

type ProtectedHomeProps = {
  user: User;
  initialWorkspaceId?: string | null;
};

export function ProtectedHome({ user, initialWorkspaceId }: ProtectedHomeProps) {
  return <WorkspaceDashboard user={user} initialWorkspaceId={initialWorkspaceId} />;
}
