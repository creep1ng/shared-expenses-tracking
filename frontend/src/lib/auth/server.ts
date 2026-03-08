import { cookies, headers } from "next/headers";

import type { AuthenticatedUserResponse } from "@/lib/auth/types";

const API_BASE_PATH = (process.env.NEXT_PUBLIC_API_BASE_PATH || "/api").replace(/\/$/, "");
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
const API_V1_PREFIX = `${API_BASE_PATH}/v1`;

type HeaderReader = {
  get(name: string): string | null;
};

function buildAbsoluteOrigin(requestHeaders: HeaderReader): string | null {
  const forwardedHost = requestHeaders.get("x-forwarded-host");
  const host = forwardedHost || requestHeaders.get("host");

  if (!host) {
    return null;
  }

  const forwardedProto = requestHeaders.get("x-forwarded-proto");
  const protocol = forwardedProto || (host.includes("localhost") ? "http" : "https");

  return `${protocol}://${host}`;
}

function buildServerApiUrl(path: string, requestHeaders: HeaderReader): string | null {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (API_ORIGIN) {
    return `${API_ORIGIN}${API_V1_PREFIX}${normalizedPath}`;
  }

  const requestOrigin = buildAbsoluteOrigin(requestHeaders);

  if (!requestOrigin) {
    return null;
  }

  return `${requestOrigin}${API_V1_PREFIX}${normalizedPath}`;
}

export async function getCurrentUserFromServer(): Promise<AuthenticatedUserResponse | null> {
  const requestHeaders = await headers();
  const cookieStore = await cookies();
  const url = buildServerApiUrl("/auth/me", requestHeaders);

  if (!url) {
    return null;
  }

  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");

  const response = await fetch(url, {
    method: "GET",
    cache: "no-store",
    headers: cookieHeader ? { cookie: cookieHeader, Accept: "application/json" } : undefined,
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    return null;
  }

  return (await response.json()) as AuthenticatedUserResponse;
}
