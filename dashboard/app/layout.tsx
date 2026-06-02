import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpsRopz — Dashboard operacional",
  description: "KPIs y alertas en tiempo real de operaciones retail",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
