import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Shared Expenses Tracking",
  description: "Base frontend en espanol para el seguimiento de gastos compartidos.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
