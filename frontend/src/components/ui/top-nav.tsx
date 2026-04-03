"use client";

import React, { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Home, ArrowRightLeft, Wallet, Tags, User as UserIcon, LogOut, ChevronDown, Plus } from "lucide-react";

import { signOut } from "@/lib/auth/api";
import type { User } from "@/lib/auth/types";
import type { Workspace } from "@/lib/workspaces/types";

type TopNavProps = {
  user: User;
  workspaces: Workspace[];
  selectedWorkspaceId: string | null;
  onSelectWorkspace: (id: string) => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
};

export function TopNav({ user, workspaces, selectedWorkspaceId, onSelectWorkspace, activeTab, onTabChange }: TopNavProps) {
  const router = useRouter();
  const [isSigningOut, startSignOutTransition] = useTransition();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);

  const handleSignOut = () => {
    startSignOutTransition(async () => {
      try {
        await signOut();
        router.replace("/sign-in");
        router.refresh();
      } catch (error) {
        console.error(error);
      }
    });
  };

  const selectedWorkspace = workspaces.find(w => w.id === selectedWorkspaceId);

  return (
    <nav className="top-nav">
      <div className="nav-links">
        <div style={{ fontWeight: 'bold', fontSize: '1.2rem', marginRight: '1rem', color: 'var(--accent-strong)' }}>
          KiloGastos
        </div>
        <button className="nav-item" data-active={activeTab === "home"} onClick={() => onTabChange("home")}>
          <Home size={18} /> Home
        </button>
        <button className="nav-item" data-active={activeTab === "movimientos"} onClick={() => onTabChange("movimientos")}>
          <ArrowRightLeft size={18} /> Movimientos
        </button>
        <button className="nav-item" data-active={activeTab === "cuentas"} onClick={() => onTabChange("cuentas")}>
          <Wallet size={18} /> Cuentas
        </button>
        <button className="nav-item" data-active={activeTab === "categorias"} onClick={() => onTabChange("categorias")}>
          <Tags size={18} /> Categorías
        </button>
      </div>

      <div className="nav-right">
        <Link className="secondary-action" href="/invitations/accept" style={{ padding: '0.4rem 0.75rem', fontSize: '0.9rem' }}>
          Aceptar invitación
        </Link>
        
        <div className="dropdown-container">
          <button 
            className="dropdown-trigger" 
            onClick={() => setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen)}
            onBlur={() => setTimeout(() => setIsWorkspaceMenuOpen(false), 200)}
          >
            {selectedWorkspace ? selectedWorkspace.name : "Seleccionar Espacio"} <ChevronDown size={16} />
          </button>
          <div className="dropdown-menu" data-open={isWorkspaceMenuOpen}>
            {workspaces.map(w => (
              <button 
                key={w.id} 
                className="dropdown-item" 
                onClick={() => {
                  onSelectWorkspace(w.id);
                  setIsWorkspaceMenuOpen(false);
                }}
              >
                {w.name}
              </button>
            ))}
            <div style={{ borderTop: '1px solid var(--surface-border)', margin: '0.5rem 0' }} />
            <button className="dropdown-item" onClick={() => router.push('/workspaces/create')}>
              <Plus size={16} /> Nuevo espacio
            </button>
          </div>
        </div>

        <div className="dropdown-container">
          <button 
            className="dropdown-trigger"
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            onBlur={() => setTimeout(() => setIsUserMenuOpen(false), 200)}
          >
            <UserIcon size={18} />
            {user.email}
          </button>
          <div className="dropdown-menu" data-open={isUserMenuOpen}>
            <button 
              className="dropdown-item dropdown-item-danger" 
              onClick={handleSignOut}
              disabled={isSigningOut}
            >
              <LogOut size={16} />
              {isSigningOut ? "Cerrando..." : "Cerrar sesión"}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
