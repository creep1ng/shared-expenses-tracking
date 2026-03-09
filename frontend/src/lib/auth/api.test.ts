import { afterEach, beforeEach, vi } from "vitest";

import { ApiError } from "@/lib/auth/errors";
import { getCurrentUser, requestPasswordReset, signIn } from "@/lib/auth/api";

const fetchMock = vi.fn();

describe("auth api helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("sends cookie-aware sign-in requests to the backend auth endpoint", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ user: { email: "user@example.com" } }),
    });

    await signIn({ email: "user@example.com", password: "secret123" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/sign-in",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        cache: "no-store",
      }),
    );
  });

  it("throws ApiError when backend returns a failure payload", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ detail: "Invalid email or password." }),
    });

    await expect(getCurrentUser()).rejects.toEqual(new ApiError("Invalid email or password.", 401));
  });

  it("returns password reset tokens when backend exposes dev responses", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({
          message: "If the account exists, a reset token has been issued.",
          reset_token: "dev-reset-token",
        }),
    });

    await expect(requestPasswordReset({ email: "user@example.com" })).resolves.toEqual({
      message: "If the account exists, a reset token has been issued.",
      reset_token: "dev-reset-token",
    });
  });
});
