"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, UserPlus, X } from "lucide-react";

import { WorkspaceCreateForm } from "@/components/workspaces/workspace-create-form";
import { createWorkspace, createWorkspaceInvitation } from "@/lib/workspaces/api";
import { getErrorMessage } from "@/lib/auth/errors";

type Notice = {
  type: "error" | "success";
  message: string;
};

export function WorkspaceCreatePage() {
  const router = useRouter();
  const [notice, setNotice] = useState<Notice | null>(null);
  const [createdWorkspace, setCreatedWorkspace] = useState<any>(null);
  const [emailsToInvite, setEmailsToInvite] = useState<string[]>([]);
  const [currentEmail, setCurrentEmail] = useState("");
  const [isInviting, setIsInviting] = useState(false);

  const handleAddEmail = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentEmail || !currentEmail.includes("@")) return;
    if (!emailsToInvite.includes(currentEmail)) {
      setEmailsToInvite([...emailsToInvite, currentEmail]);
    }
    setCurrentEmail("");
  };

  const handleRemoveEmail = (emailToRemove: string) => {
    setEmailsToInvite(emailsToInvite.filter(e => e !== emailToRemove));
  };

  const handleCreate = async (values: { name: string; type: "personal" | "shared" }) => {
    setNotice(null);

    try {
      const workspace = await createWorkspace(values);
      setCreatedWorkspace(workspace);
      return true;
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
      return false;
    }
  };

  const handleSkip = () => {
    router.push(`/?workspace=${createdWorkspace.id}`);
  };

  const handleInviteMembers = async () => {
    setIsInviting(true);
    try {
      if (emailsToInvite.length > 0) {
        await Promise.allSettled(
          emailsToInvite.map(email => createWorkspaceInvitation(createdWorkspace.id, { email }))
        );
      }
      router.push(`/?workspace=${createdWorkspace.id}`);
    } catch (error) {
      setNotice({ type: "error", message: getErrorMessage(error) });
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <>
      <nav className="top-nav">
        <div className="nav-links">
          <div style={{ fontWeight: 'bold', fontSize: '1.2rem', color: 'var(--accent-strong)' }}>
            KiloGastos
          </div>
          <button className="nav-item" onClick={() => router.push("/")}>
            <ArrowLeft size={18} /> Volver
          </button>
        </div>
      </nav>

      <main className="main-content" style={{ maxWidth: '600px', marginTop: '2rem' }}>
        <section className="workspace-dashboard-card" style={{ padding: '2rem' }}>
          {!createdWorkspace ? (
            <>
              <header className="workspace-form-header">
                <h1 className="dashboard-title">Crear Nuevo Espacio</h1>
                <p className="dashboard-copy" style={{ marginTop: '0.5rem' }}>
                  Configura un nuevo espacio de trabajo. Puedes ser personal o compartido.
                </p>
              </header>

              {notice ? (
                <div
                  className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
                  role={notice.type === "error" ? "alert" : "status"}
                  style={{ marginBottom: '2rem' }}
                >
                  {notice.message}
                </div>
              ) : null}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <WorkspaceCreateForm onCreate={handleCreate} />
              </div>
            </>
          ) : (
            <>
              <header className="workspace-form-header">
                <h1 className="dashboard-title">¡Espacio creado!</h1>
                <p className="dashboard-copy" style={{ marginTop: '0.5rem' }}>
                  Tu espacio {createdWorkspace.name} ha sido creado exitosamente.
                </p>
              </header>

              {notice ? (
                <div
                  className={`auth-feedback ${notice.type === "error" ? "auth-feedback-error" : "auth-feedback-success"}`}
                  role={notice.type === "error" ? "alert" : "status"}
                  style={{ marginBottom: '1.5rem' }}
                >
                  {notice.message}
                </div>
              ) : null}

              <div className="workspace-panel" style={{ marginTop: '1.5rem', padding: '1.5rem', background: 'var(--background)', border: '1px solid var(--surface-border)' }}>
                <div className="workspace-form-header">
                  <h3 className="workspace-section-title" style={{ fontSize: '1.1rem' }}>¿Quieres invitar miembros ahora?</h3>
                  <p className="workspace-section-copy" style={{ marginBottom: '1rem' }}>
                    Añade correos electrónicos de las personas que deseas invitar a este espacio.
                  </p>
                </div>

                <form onSubmit={handleAddEmail} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                  <input
                    type="email"
                    placeholder="correo@ejemplo.com"
                    className="auth-input"
                    value={currentEmail}
                    onChange={(e) => setCurrentEmail(e.target.value)}
                    style={{ flex: 1 }}
                  />
                  <button type="submit" className="secondary-action" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <UserPlus size={16} /> Añadir
                  </button>
                </form>

                {emailsToInvite.length > 0 && (
                  <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {emailsToInvite.map(email => (
                      <li key={email} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 1rem', background: 'var(--surface-strong)', borderRadius: '0.5rem' }}>
                        <span style={{ fontSize: '0.9rem' }}>{email}</span>
                        <button type="button" onClick={() => handleRemoveEmail(email)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--danger)' }}>
                          <X size={16} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  <button 
                    className="secondary-action" 
                    onClick={handleSkip}
                    disabled={isInviting}
                  >
                    Omitir por ahora
                  </button>
                  <button 
                    className="primary-action" 
                    onClick={handleInviteMembers}
                    disabled={isInviting}
                  >
                    {isInviting ? "Enviando invitaciones..." : "Invitar miembros"}
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}
