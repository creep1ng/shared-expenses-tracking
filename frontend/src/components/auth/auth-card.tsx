import React from "react";
import type { ReactNode } from "react";

type AuthCardProps = {
  children: ReactNode;
  eyebrow: string;
  title: string;
  description: string;
};

export function AuthCard({ children, eyebrow, title, description }: AuthCardProps) {
  return (
    <section className="auth-card">
      <div className="auth-intro">
        <span className="auth-eyebrow">{eyebrow}</span>
        <h1 className="auth-title">{title}</h1>
        <p className="auth-description">{description}</p>
      </div>
      {children}
    </section>
  );
}
