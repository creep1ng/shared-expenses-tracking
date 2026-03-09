import { redirect } from "next/navigation";

import { ProtectedHome } from "@/components/auth/protected-home";
import { getCurrentUserFromServer } from "@/lib/auth/server";

type HomePageProps = {
  searchParams?: Promise<{
    workspace?: string;
  }>;
};

export default async function Home({ searchParams }: HomePageProps) {
  const auth = await getCurrentUserFromServer();
  const params = searchParams ? await searchParams : undefined;

  if (!auth) {
    redirect("/sign-in?redirect=/");
  }

  return <ProtectedHome user={auth.user} initialWorkspaceId={params?.workspace ?? null} />;
}
