import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "../components/site-header";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading"
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body"
});

export const metadata: Metadata = {
  title: {
    default: "Crypto Intelligence | Setups PRO crypto con alertas Telegram",
    template: "%s | Crypto Intelligence"
  },
  description:
    "Plataforma de Setups PRO crypto para trading táctico: confluencia, estado operativo, confirmaciones, plan indicativo, alertas Telegram y dashboard con histórico.",
  openGraph: {
    title: "Crypto Intelligence | Setups PRO crypto con alertas Telegram",
    description:
      "Setups PRO accionables para trading táctico y swing corto. Menos ruido, más contexto operativo y alertas inmediatas por Telegram.",
    type: "website"
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={`${headingFont.variable} ${bodyFont.variable} bg-canvas text-ink antialiased`}>
        <div className="relative min-h-screen overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[32rem] bg-[radial-gradient(circle_at_top,rgba(185,255,105,0.18),transparent_55%),radial-gradient(circle_at_30%_20%,rgba(96,216,191,0.16),transparent_32%)]" />
          <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 pb-12 pt-6 sm:px-8 lg:px-10">
            <SiteHeader />
            <main className="flex-1">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
