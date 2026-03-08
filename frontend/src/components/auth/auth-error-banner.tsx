import React from "react";

type AuthErrorBannerProps = {
  message?: string | null;
};

export function AuthErrorBanner({ message }: AuthErrorBannerProps) {
  if (!message) {
    return null;
  }

  return (
    <div className="auth-feedback auth-feedback-error" role="alert">
      {message}
    </div>
  );
}
