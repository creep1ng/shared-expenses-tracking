import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Shared Expenses Tracking",
  description: "Base frontend en español para el seguimiento de gastos compartidos.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
  },
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
