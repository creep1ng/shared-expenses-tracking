import { cookies } from "next/headers";
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
  const urlToken = params?.token;

  if (urlToken && urlToken.length >= 20) {
    redirect(`/invitations?token=${encodeURIComponent(urlToken)}`);
  }

  const cookieStore = await cookies();
  const cookieToken = cookieStore.get("pending_invitation_token")?.value ?? null;

  if (!auth) {
    redirect("/sign-in?redirect=%2Finvitations%2Faccept");
  }

  return (
    <AuthShell>
      <InvitationAcceptForm initialToken={cookieToken} />
    </AuthShell>
  );
}
