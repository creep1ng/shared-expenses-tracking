import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { InvitationAcceptForm } from "@/components/workspaces/invitation-accept-form";

const replaceMock = vi.fn();
const refreshMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock,
    refresh: refreshMock,
  }),
  useSearchParams: () => new URLSearchParams("token=query-token-12345678901234567890"),
}));

const acceptWorkspaceInvitationMock = vi.fn();

vi.mock("@/lib/workspaces/api", () => ({
  acceptWorkspaceInvitation: (...args: unknown[]) => acceptWorkspaceInvitationMock(...args),
}));

describe("InvitationAcceptForm", () => {
  const originalSetTimeout = window.setTimeout;
  const setTimeoutSpy = vi.spyOn(window, "setTimeout");

  beforeEach(() => {
    replaceMock.mockReset();
    refreshMock.mockReset();
    acceptWorkspaceInvitationMock.mockReset();
    setTimeoutSpy.mockImplementation(((callback: TimerHandler, delay?: number) => {
      if (delay === 900 && typeof callback === "function") {
        queueMicrotask(() => {
          callback();
        });
        return 0;
      }

      return originalSetTimeout(callback, delay);
    }) as typeof window.setTimeout);
  });

  afterEach(() => {
    setTimeoutSpy.mockRestore();
  });

  it("prefills the token from the query string and redirects after success", async () => {
    const user = userEvent.setup();

    acceptWorkspaceInvitationMock.mockResolvedValue({
      workspace: {
        id: "workspace-99",
        name: "Viaje a Madrid",
      },
    });

    render(<InvitationAcceptForm />);

    expect(screen.getByLabelText(/token de invitacion/i)).toHaveValue(
      "query-token-12345678901234567890",
    );

    await user.click(screen.getByRole("button", { name: /aceptar invitacion/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(/te has unido a viaje a madrid/i);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/?workspace=workspace-99");
      expect(refreshMock).toHaveBeenCalled();
    });
  });
});
