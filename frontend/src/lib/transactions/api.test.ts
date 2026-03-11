import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { uploadTransactionReceipt } from "@/lib/transactions/api";

const fetchMock = vi.fn();

describe("transactions api helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("sends receipt uploads with the backend multipart field name", async () => {
    const file = new File(["receipt-bytes"], "ticket.pdf", {
      type: "application/pdf",
    });

    fetchMock.mockResolvedValue({ ok: true });

    await uploadTransactionReceipt("workspace-1", "tx-1", file);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/workspaces/workspace-1/transactions/tx-1/receipt",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        cache: "no-store",
      }),
    );

    const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const body = requestInit.body;

    expect(body).toBeInstanceOf(FormData);

    const formData = body as FormData;
    const headers = requestInit.headers as Headers;

    expect(formData.get("receipt")).toBe(file);
    expect(formData.get("file")).toBeNull();
    expect(headers.get("Content-Type")).toBeNull();
  });
});
