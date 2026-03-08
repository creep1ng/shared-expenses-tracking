import { ApiError, getErrorMessage, parseApiError } from "@/lib/auth/errors";

describe("auth errors", () => {
  it("returns backend detail string when present", () => {
    const error = parseApiError({ detail: "Invalid email or password." }, 401);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe("Invalid email or password.");
    expect(error.status).toBe(401);
  });

  it("joins validation messages when detail is a list", () => {
    const error = parseApiError(
      {
        detail: [{ msg: "Campo requerido." }, { msg: "Correo invalido." }],
      },
      422,
    );

    expect(error.message).toBe("Campo requerido. Correo invalido.");
  });

  it("normalizes unknown errors", () => {
    expect(getErrorMessage(new Error("Fallo local"))).toBe("Fallo local");
    expect(getErrorMessage(null)).toMatch(/ocurrio un error inesperado/i);
  });
});
