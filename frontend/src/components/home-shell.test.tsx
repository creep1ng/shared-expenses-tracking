import React from "react";
import { render, screen } from "@testing-library/react";

import { HomeShell } from "@/components/home-shell";

describe("HomeShell", () => {
  it("renders the spanish landing content", () => {
    render(<HomeShell />);

    expect(
      screen.getByRole("heading", {
        name: /gastos compartidos, base lista para crecer/i,
      }),
    ).toBeInTheDocument();

    expect(screen.getByRole("link", { name: /ver health check/i })).toHaveAttribute(
      "href",
      "/api/v1/health",
    );
  });
});
