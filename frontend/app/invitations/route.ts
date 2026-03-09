import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get("token");

  if (!token || token.length < 20) {
    redirect("/invitations/accept");
  }

  const cookieStore = await cookies();

  cookieStore.set("pending_invitation_token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 10,
    path: "/",
  });

  redirect("/sign-in?redirect=%2Finvitations%2Faccept");
}
