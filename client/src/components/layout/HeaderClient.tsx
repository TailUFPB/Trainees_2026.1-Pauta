"use client";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { useLoginModal } from "@/components/auth/LoginModalProvider";
import { useSession } from "@/lib/hooks/useSession";
import { createClient } from "@/lib/supabase/client";
import { NAV_CONTA, NAV_PRINCIPAL } from "@/lib/nav";
import { MobileNav } from "./MobileNav";

interface Props {
  initialUserEmail: string | null;
}

export function HeaderClient({ initialUserEmail }: Props) {
  const { user } = useSession();
  const { open } = useLoginModal();
  const email = user?.email ?? initialUserEmail;

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  };

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
          {NAV_PRINCIPAL.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-text-muted transition-colors hover:bg-surface hover:text-text"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto hidden items-center gap-2 md:flex">
          {email ? (
            <div className="flex items-center gap-2">
              <NotificationBell />
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                <button
                  className="inline-flex h-9 items-center gap-2 rounded-pill border border-border px-3 text-sm text-text transition-colors hover:border-text"
                  aria-label="Menu da conta"
                >
                  <span className="grid h-6 w-6 place-items-center rounded-pill bg-accent text-xs font-semibold text-white">
                    {email[0]?.toUpperCase() ?? "?"}
                  </span>
                  <span className="max-w-[140px] truncate">{email}</span>
                </button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                <DropdownMenu.Content
                  align="end"
                  sideOffset={8}
                  className="z-50 w-56 rounded-md border border-border bg-surface p-1.5 shadow-[var(--shadow-2)]"
                >
                  {NAV_CONTA.map((item) => (
                    <DropdownMenu.Item key={item.href} asChild>
                      <Link
                        href={item.href}
                        className="block rounded-sm px-3 py-2 text-sm text-text outline-none hover:bg-bg data-[highlighted]:bg-bg"
                      >
                        {item.label}
                      </Link>
                    </DropdownMenu.Item>
                  ))}
                  <DropdownMenu.Separator className="my-1 h-px bg-border" />
                  <DropdownMenu.Item
                    onSelect={handleSignOut}
                    className="cursor-pointer rounded-sm px-3 py-2 text-sm text-danger outline-none hover:bg-bg data-[highlighted]:bg-bg"
                  >
                    Sair
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            </div>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => open()}>
              Entrar
            </Button>
          )}
        </div>
        <MobileNav
          email={email}
          onSignIn={() => open()}
          onSignOut={handleSignOut}
        />
      </Container>
    </header>
  );
}
