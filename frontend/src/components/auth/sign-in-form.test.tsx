import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SignInForm } from "@/components/auth/sign-in-form";

const replaceMock = vi.fn();
const refreshMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock,
    refresh: refreshMock,
  }),
  useSearchParams: () => new URLSearchParams(),
}));

const signInMock = vi.fn();

vi.mock("@/lib/auth/api", () => ({
  signIn: (...args: unknown[]) => signInMock(...args),
}));

describe("SignInForm", () => {
  beforeEach(() => {
    signInMock.mockReset();
    replaceMock.mockReset();
    refreshMock.mockReset();
  });

  it("shows validation messages before submitting", async () => {
    const user = userEvent.setup();

    render(<SignInForm />);

    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByText(/correo electronico valido/i)).toBeInTheDocument();
    expect(screen.getByText(/al menos 8 caracteres/i)).toBeInTheDocument();
  });

  it("shows backend errors returned by the API", async () => {
    const user = userEvent.setup();
    signInMock.mockRejectedValue(new Error("Invalid email or password."));

    render(<SignInForm />);

    await user.type(screen.getByLabelText(/correo electronico/i), "user@example.com");
    await user.type(screen.getByLabelText(/^contrasena$/i), "secret123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid email or password/i);
  });

  it("redirects to the protected root after success", async () => {
    const user = userEvent.setup();
    signInMock.mockResolvedValue({ user: { email: "user@example.com" } });

    render(<SignInForm />);

    await user.type(screen.getByLabelText(/correo electronico/i), "user@example.com");
    await user.type(screen.getByLabelText(/^contrasena$/i), "secret123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/");
      expect(refreshMock).toHaveBeenCalled();
    });
  });
});
