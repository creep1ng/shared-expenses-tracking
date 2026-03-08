import { parseApiError } from "@/lib/auth/errors";
import type {
  AuthenticatedUserResponse,
  MessageResponse,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
  PasswordResetRequestResponse,
  SignInPayload,
  SignUpPayload,
} from "@/lib/auth/types";

const API_BASE_PATH = (process.env.NEXT_PUBLIC_API_BASE_PATH || "/api").replace(/\/$/, "");
const API_ORIGIN = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
  /\/$/, "",
);
const API_V1_PREFIX = `${API_BASE_PATH}/v1`;

type ErrorResponse = {
  detail?: string | { message?: string } | Array<{ msg?: string }>;
  message?: string;
};

type JsonCapableResponse = Response & {
  json?: () => Promise<unknown>;
  text?: () => Promise<string>;
};

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = API_ORIGIN ? `${API_ORIGIN}${API_V1_PREFIX}` : API_V1_PREFIX;

  return `${base}${normalizedPath}`;
}

async function getErrorFromResponse(response: Response): Promise<string> {
  try {
    const payload = (await readJson(response)) as ErrorResponse;

    return parseApiError(payload, response.status).message;
  } catch {
    // Ignore JSON parsing failures and fall back to a generic message.
  }

  return `La solicitud fallo con estado ${response.status}.`;
}

async function readJson<T>(response: Response): Promise<T> {
  const jsonResponse = response as JsonCapableResponse;

  if (typeof jsonResponse.json === "function") {
    return (await jsonResponse.json()) as T;
  }

  if (typeof jsonResponse.text === "function") {
    return JSON.parse(await jsonResponse.text()) as T;
  }

  throw new TypeError("Response body is not readable as JSON.");
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    cache: "no-store",
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw parseApiError({ detail: await getErrorFromResponse(response) }, response.status);
  }

  return await readJson<T>(response);
}

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
