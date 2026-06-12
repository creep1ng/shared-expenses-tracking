"use client";

import React, { useState, useTransition, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Home, ArrowRightLeft, Wallet, Tags, User as UserIcon, LogOut, ChevronDown, Plus, ChevronLeft, ChevronRight, Briefcase, Mail } from "lucide-react";

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
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  const navLinksRef = useRef<HTMLDivElement>(null);

  const checkScroll = () => {
    if (navLinksRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = navLinksRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 5);
    }
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener("resize", checkScroll);
    return () => window.removeEventListener("resize", checkScroll);
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsWorkspaceMenuOpen(false);
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const scrollLeft = () => {
    if (navLinksRef.current) {
      navLinksRef.current.scrollBy({ left: -100, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (navLinksRef.current) {
      navLinksRef.current.scrollBy({ left: 100, behavior: "smooth" });
    }
  };

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

  const selectedWorkspace = workspaces.find((workspace) => workspace.id === selectedWorkspaceId);

  return (
    <>
      <nav className="top-nav">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", minWidth: "0", flex: 1 }}>
          {showLeftArrow && (
            <button 
              className="nav-item" 
              onClick={scrollLeft}
              aria-label="Desplazar navegación a la izquierda"
              style={{ padding: "0.5rem", flexShrink: 0 }}
            >
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
          )}
          <div className="nav-links" ref={navLinksRef} onScroll={checkScroll}>
            <div style={{ fontWeight: "bold", fontSize: "1.2rem", marginRight: "1rem", color: "var(--accent-strong)", flexShrink: 0 }}>
              KiloGastos
            </div>
            <button className="nav-item" data-active={activeTab === "home"} aria-label="Inicio" aria-current={activeTab === "home" ? "page" : undefined} onClick={() => onTabChange("home")}>
              <Home size={18} aria-hidden="true" /> <span className="desktop-only">Inicio</span>
            </button>
            <button className="nav-item" data-active={activeTab === "movimientos"} aria-label="Movimientos" aria-current={activeTab === "movimientos" ? "page" : undefined} onClick={() => onTabChange("movimientos")}>
              <ArrowRightLeft size={18} aria-hidden="true" /> <span className="desktop-only">Movimientos</span>
            </button>
            <button className="nav-item" data-active={activeTab === "cuentas"} aria-label="Cuentas" aria-current={activeTab === "cuentas" ? "page" : undefined} onClick={() => onTabChange("cuentas")}>
              <Wallet size={18} aria-hidden="true" /> <span className="desktop-only">Cuentas</span>
            </button>
            <button className="nav-item" data-active={activeTab === "categorias"} aria-label="Categorías" aria-current={activeTab === "categorias" ? "page" : undefined} onClick={() => onTabChange("categorias")}>
              <Tags size={18} aria-hidden="true" /> <span className="desktop-only">Categorías</span>
            </button>
          </div>
          {showRightArrow && (
            <button 
              className="nav-item" 
              onClick={scrollRight}
              aria-label="Desplazar navegación a la derecha"
              style={{ padding: "0.5rem", flexShrink: 0 }}
            >
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          )}
        </div>

        <div className="nav-right desktop-only">
          <Link className="secondary-action" href="/invitations/accept" style={{ padding: "0.4rem 0.75rem", fontSize: "0.9rem" }}>
            Aceptar invitación
          </Link>
          
          <div className="dropdown-container">
            <button 
              className="dropdown-trigger" 
              onClick={() => {
                setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen);
                setIsUserMenuOpen(false);
              }}
              onBlur={() => setTimeout(() => setIsWorkspaceMenuOpen(false), 200)}
              aria-haspopup="menu"
              aria-expanded={isWorkspaceMenuOpen}
              aria-controls="desktop-workspace-menu"
            >
              {selectedWorkspace ? selectedWorkspace.name : "Seleccionar espacio"} <ChevronDown size={16} aria-hidden="true" />
            </button>
            <div id="desktop-workspace-menu" className="dropdown-menu" data-open={isWorkspaceMenuOpen} role="menu">
              {workspaces.map((workspace) => (
                <button 
                  key={workspace.id}
                  className="dropdown-item" 
                  role="menuitem"
                  aria-current={workspace.id === selectedWorkspaceId ? "true" : undefined}
                  onClick={() => {
                    onSelectWorkspace(workspace.id);
                    setIsWorkspaceMenuOpen(false);
                  }}
                >
                  {workspace.name}
                </button>
              ))}
              <div style={{ borderTop: "1px solid var(--surface-border)", margin: "0.5rem 0" }} />
              <button className="dropdown-item" role="menuitem" onClick={() => router.push("/workspaces/create")}>
                <Plus size={16} aria-hidden="true" /> Nuevo espacio
              </button>
            </div>
          </div>

          <div className="dropdown-container">
            <button 
              className="dropdown-trigger"
              onClick={() => {
                setIsUserMenuOpen(!isUserMenuOpen);
                setIsWorkspaceMenuOpen(false);
              }}
              onBlur={() => setTimeout(() => setIsUserMenuOpen(false), 200)}
              aria-haspopup="menu"
              aria-expanded={isUserMenuOpen}
              aria-controls="desktop-user-menu"
            >
              <UserIcon size={18} aria-hidden="true" />
              {user.email}
            </button>
            <div id="desktop-user-menu" className="dropdown-menu" data-open={isUserMenuOpen} role="menu">
              <button 
                className="dropdown-item dropdown-item-danger" 
                role="menuitem"
                onClick={handleSignOut}
                disabled={isSigningOut}
              >
                <LogOut size={16} aria-hidden="true" />
                {isSigningOut ? "Cerrando..." : "Cerrar sesión"}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Bottom Navigation */}
      <nav className="bottom-nav">
        <div className="bottom-nav-item">
          <button 
            className="nav-item"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsWorkspaceMenuOpen((isOpen) => !isOpen);
              setIsUserMenuOpen(false);
            }}
            aria-label="Abrir selector de espacios"
            aria-haspopup="menu"
            aria-expanded={isWorkspaceMenuOpen}
            aria-controls="mobile-workspace-menu"
          >
            <Briefcase size={22} aria-hidden="true" />
          </button>
        </div>

        <div className="bottom-nav-item">
          <Link className="nav-item" href="/invitations/accept" aria-label="Aceptar invitación">
            <Mail size={22} aria-hidden="true" />
          </Link>
        </div>

        <div className="bottom-nav-item">
          <button 
            className="nav-item"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsUserMenuOpen((isOpen) => !isOpen);
              setIsWorkspaceMenuOpen(false);
            }}
            aria-label="Abrir menú de usuario"
            aria-haspopup="menu"
            aria-expanded={isUserMenuOpen}
            aria-controls="mobile-user-menu"
          >
            <UserIcon size={22} aria-hidden="true" />
          </button>
        </div>
      </nav>

      {/* Overlay dropdowns for mobile */}
      {isWorkspaceMenuOpen && (
        <div className="dropdown-overlay" onClick={(e) => {
          e.stopPropagation();
          setIsWorkspaceMenuOpen(false);
        }}>
          <div id="mobile-workspace-menu" className="dropdown-menu mobile-dropdown" data-open={isWorkspaceMenuOpen} role="menu" onClick={(e) => e.stopPropagation()}>
            {workspaces.map((workspace) => (
              <button 
                key={workspace.id}
                className="dropdown-item" 
                role="menuitem"
                aria-current={workspace.id === selectedWorkspaceId ? "true" : undefined}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectWorkspace(workspace.id);
                  setIsWorkspaceMenuOpen(false);
                }}
              >
                {workspace.name}
              </button>
            ))}
            <div style={{ borderTop: "1px solid var(--surface-border)", margin: "0.5rem 0" }} />
            <button className="dropdown-item" role="menuitem" onClick={(e) => {
              e.stopPropagation();
              router.push("/workspaces/create");
              setIsWorkspaceMenuOpen(false);
            }}>
              <Plus size={16} aria-hidden="true" /> Nuevo espacio
            </button>
          </div>
        </div>
      )}

      {isUserMenuOpen && (
        <div className="dropdown-overlay" onClick={(e) => {
          e.stopPropagation();
          setIsUserMenuOpen(false);
        }}>
          <div id="mobile-user-menu" className="dropdown-menu mobile-dropdown" data-open={isUserMenuOpen} role="menu" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: "0.75rem 1rem", borderBottom: "1px solid var(--surface-border)" }}>
              <p style={{ fontWeight: 700, margin: 0 }}>{user.email}</p>
            </div>
            <button 
              className="dropdown-item dropdown-item-danger" 
              role="menuitem"
              onClick={(e) => {
                e.stopPropagation();
                handleSignOut();
                setIsUserMenuOpen(false);
              }}
              disabled={isSigningOut}
            >
              <LogOut size={16} aria-hidden="true" />
              {isSigningOut ? "Cerrando..." : "Cerrar sesión"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
