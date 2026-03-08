import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { InvitationAcceptForm } from "@/components/workspaces/invitation-accept-form";
import { getCurrentUserFromServer } from "@/lib/auth/server";

type AcceptInvitationPageProps = {
  searchParams?: Promise<{
    token?: string;
  }>;
};

export default async function AcceptInvitationPage({ searchParams }: AcceptInvitationPageProps) {
  const auth = await getCurrentUserFromServer();
  const params = searchParams ? await searchParams : undefined;

  if (!auth) {
    const redirectTarget = params?.token
      ? `/invitations/accept?token=${encodeURIComponent(params.token)}`
      : "/invitations/accept";

    redirect(`/sign-in?redirect=${encodeURIComponent(redirectTarget)}`);
  }

  return (
    <AuthShell>
      <InvitationAcceptForm />
    </AuthShell>
  );
}
