import { requestJson } from "@/lib/api/client";
import type {
  AuthenticatedUserResponse,
  MessageResponse,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
  PasswordResetRequestResponse,
  SignInPayload,
  SignUpPayload,
} from "@/lib/auth/types";

export function getCurrentUser(): Promise<AuthenticatedUserResponse> {
  return requestJson<AuthenticatedUserResponse>("/auth/me", {
    method: "GET",
  });
}

export function signUp(payload: SignUpPayload): Promise<AuthenticatedUserResponse["user"]> {
  return requestJson<AuthenticatedUserResponse["user"]>("/auth/sign-up", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function signIn(payload: SignInPayload): Promise<AuthenticatedUserResponse> {
  return requestJson<AuthenticatedUserResponse>("/auth/sign-in", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function signOut(): Promise<MessageResponse> {
  return requestJson<MessageResponse>("/auth/sign-out", {
    method: "POST",
  });
}

export function requestPasswordReset(
  payload: PasswordResetRequestPayload,
): Promise<PasswordResetRequestResponse> {
  return requestJson<PasswordResetRequestResponse>("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmPasswordReset(
  payload: PasswordResetConfirmPayload,
): Promise<MessageResponse> {
  return requestJson<MessageResponse>("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
