import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordResetConfirmForm } from "@/components/auth/password-reset-confirm-form";

export default function PasswordResetConfirmPage() {
  return (
    <AuthShell>
      <PasswordResetConfirmForm />
    </AuthShell>
  );
}
