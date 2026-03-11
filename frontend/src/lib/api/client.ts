import { parseApiError } from "@/lib/auth/errors";

const API_BASE_PATH = (process.env.NEXT_PUBLIC_API_BASE_PATH || "/api").replace(/\/$/, "");
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "";
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

async function getErrorFromResponse(response: Response): Promise<string> {
  try {
    const payload = (await readJson(response)) as ErrorResponse;

    return parseApiError(payload, response.status).message;
  } catch {
    return `La solicitud fallo con estado ${response.status}.`;
  }
}

function isFormDataBody(body: BodyInit | null | undefined): body is FormData {
  return typeof FormData !== "undefined" && body instanceof FormData;
}

function buildRequestHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers ?? {});

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (init?.body && !isFormDataBody(init.body) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return headers;
}

async function performRequest(path: string, init?: RequestInit): Promise<Response> {
  return await fetch(buildApiUrl(path), {
    ...init,
    cache: "no-store",
    credentials: "include",
    headers: buildRequestHeaders(init),
  });
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await performRequest(path, init);

  if (!response.ok) {
    throw parseApiError({ detail: await getErrorFromResponse(response) }, response.status);
  }

  return await readJson<T>(response);
}

export async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const response = await performRequest(path, init);

  if (!response.ok) {
    throw parseApiError({ detail: await getErrorFromResponse(response) }, response.status);
  }
}
