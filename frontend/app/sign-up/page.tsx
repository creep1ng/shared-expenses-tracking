import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { SignUpForm } from "@/components/auth/sign-up-form";
import { getCurrentUserFromServer } from "@/lib/auth/api";

export default async function SignUpPage() {
  const auth = await getCurrentUserFromServer();

  if (auth) {
    redirect("/");
  }

  return (
    <AuthShell>
      <SignUpForm />
    </AuthShell>
  );
}
