import { WorkspaceCreatePage } from "@/components/workspaces/workspace-create-page";
import { getCurrentUserFromServer } from "@/lib/auth/server";
import { redirect } from "next/navigation";

export default async function CreateWorkspace() {
  const auth = await getCurrentUserFromServer();

  if (!auth) {
    redirect("/sign-in?redirect=/workspaces/create");
  }

  return <WorkspaceCreatePage />;
}
