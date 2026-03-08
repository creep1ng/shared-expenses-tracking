import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { SignInForm } from "@/components/auth/sign-in-form";
import { getCurrentUserFromServer } from "@/lib/auth/server";

export default async function SignInPage() {
  const auth = await getCurrentUserFromServer();

  if (auth) {
    redirect("/");
  }

  return (
    <AuthShell>
      <SignInForm />
    </AuthShell>
  );
}
