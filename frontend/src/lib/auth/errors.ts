export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type ApiErrorPayload = {
  detail?: string | { message?: string } | Array<{ msg?: string }>;
  message?: string;
};

export function parseApiError(payload: ApiErrorPayload | null | undefined, status: number): ApiError {
  if (typeof payload?.detail === "string" && payload.detail.trim().length > 0) {
    return new ApiError(payload.detail, status);
  }

  if (Array.isArray(payload?.detail)) {
    const messages = payload.detail
      .map((item) => (typeof item?.msg === "string" ? item.msg.trim() : ""))
      .filter((message) => message.length > 0);

    if (messages.length > 0) {
      return new ApiError(messages.join(" "), status);
    }
  }

  if (
    payload?.detail &&
    typeof payload.detail === "object" &&
    !Array.isArray(payload.detail) &&
    typeof payload.detail.message === "string" &&
    payload.detail.message.trim().length > 0
  ) {
    return new ApiError(payload.detail.message, status);
  }

  if (typeof payload?.message === "string" && payload.message.trim().length > 0) {
    return new ApiError(payload.message, status);
  }

  return new ApiError(`La solicitud fallo con estado ${status}.`, status);
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  if (typeof error === "string" && error.trim().length > 0) {
    return error;
  }

  return "Ocurrio un error inesperado. Intenta de nuevo.";
}

export { ApiError as AuthApiError };
