import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Pauta",
  description: "Transparência política municipal — mapeie problemas e conheça candidatos.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="pt-BR"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900">
        <header className="border-b border-zinc-200 bg-white">
          <nav className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
            <Link href="/" className="font-semibold tracking-tight">
              Pauta
            </Link>
            <div className="flex gap-4 text-sm text-zinc-600">
              <Link href="/mapa" className="hover:text-zinc-900">Mapa</Link>
              <Link href="/reportar" className="hover:text-zinc-900">Reportar</Link>
              <Link href="/recomendacoes" className="hover:text-zinc-900">Candidatos</Link>
            </div>
            <Link href="/login" className="ml-auto text-sm text-zinc-600 hover:text-zinc-900">
              Entrar
            </Link>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
