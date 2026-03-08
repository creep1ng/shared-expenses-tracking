import { redirect } from "next/navigation";

import { ProtectedHome } from "@/components/auth/protected-home";
import { getCurrentUserFromServer } from "@/lib/auth/server";

export default async function Home() {
  const auth = await getCurrentUserFromServer();

  if (!auth) {
    redirect("/sign-in?redirect=/");
  }

  return <ProtectedHome user={auth.user} />;
}
