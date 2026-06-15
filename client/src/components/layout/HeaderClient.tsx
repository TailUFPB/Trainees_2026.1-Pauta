"use client";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { useLoginModal } from "@/components/auth/LoginModalProvider";
import { NAV_PUBLICO } from "@/lib/nav";
import { MobileNav } from "./MobileNav";

// Top bar do visitante deslogado. Logados usam o AppShell (sidebar), então aqui
// não há sino nem menu de conta — apenas navegação de leitura + "Entrar".
export function HeaderClient() {
  const { open } = useLoginModal();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg/80 backdrop-blur supports-[backdrop-filter]:bg-bg/70">
      <Container className="flex h-16 items-center gap-6">
        <Link
          href="/"
          className="rounded-md outline-none focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Pauta — página inicial"
        >
          <Logo />
        </Link>
        <nav className="hidden gap-1 md:flex" aria-label="Navegação principal">
          {NAV_PUBLICO.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-text-muted transition-colors hover:bg-surface hover:text-text"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto hidden md:flex">
          <Button variant="primary" size="sm" onClick={() => open()}>
            Entrar
          </Button>
        </div>
        <MobileNav onSignIn={() => open()} />
      </Container>
    </header>
  );
}
