import React from "react";

const highlights = [
  {
    label: "Estado",
    value: "Base lista",
    copy: "La aplicacion arranca con Next.js, Tailwind y TypeScript configurados.",
  },
  {
    label: "Idioma",
    value: "es",
    copy: "El layout y el contenido inicial estan preparados para una experiencia en espanol.",
  },
  {
    label: "Pruebas",
    value: "Vitest",
    copy: "Existe una prueba simple para validar el esqueleto del frontend.",
  },
  {
    label: "Salud",
    value: "/api/v1/health",
    copy: "Hay una ruta minima para integraciones de arranque y verificacion basica.",
  },
];

export function HomeShell() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <div className="hero-grid">
          <div>
            <span className="eyebrow">Frontend foundation</span>
            <h1 className="hero-title">Gastos compartidos, base lista para crecer.</h1>
            <p className="hero-copy">
              Este esqueleto inicial prepara la aplicacion web para los siguientes hitos del
              producto: autenticacion, espacios de trabajo y registro de movimientos.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="/api/v1/health">
                Ver health check
              </a>
              <a className="secondary-action" href="https://nextjs.org/docs">
                Revisar stack base
              </a>
            </div>
          </div>

          <div className="stats-grid" aria-label="Resumen del frontend base">
            {highlights.map((item) => (
              <article className="stat-card" key={item.label}>
                <span className="stat-label">{item.label}</span>
                <span className="stat-value">{item.value}</span>
                <p className="stat-copy">{item.copy}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
