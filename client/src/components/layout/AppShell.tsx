"use client";
import * as Dialog from "@radix-ui/react-dialog";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Camera, Map, Menu, Newspaper, User, Users, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { NotificationBell } from "@/components/notifications/NotificationBell";
import { NAV_APP, NAV_CONTA, type NavItem } from "@/lib/nav";
import { createClient } from "@/lib/supabase/client";

// CONTA sem `exact`: mantém "Minha conta" ativo em todas as sub-rotas (/conta/*).
const CONTA: NavItem = { href: "/conta", label: "Minha conta" };
const ITENS: readonly NavItem[] = [...NAV_APP, CONTA];

const ICON_BY_HREF: Record<string, LucideIcon> = {
  "/feed": Newspaper,
  "/mapa": Map,
  "/reportar": Camera,
  "/candidatos": Users,
  "/conta": User,
};

function isActive(path: string, item: NavItem): boolean {
  if (item.exact) return path === item.href;
  return path === item.href || path.startsWith(item.href + "/");
}

function SidebarLinks({ onNavigate }: { onNavigate?: () => void }) {
  const path = usePathname();
  return (
    <nav className="flex flex-col gap-1" aria-label="Navegação do app">
      {ITENS.map((item) => {
        const Icon = ICON_BY_HREF[item.href] ?? Newspaper;
        const active = isActive(path, item);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={
              "inline-flex min-h-[44px] items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors " +
              (active
                ? "bg-surface text-text"
                : "text-text-muted hover:bg-surface hover:text-text")
            }
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({
  email,
  children,
}: {
  email: string | null;
  children: React.ReactNode;
}) {
  const [drawer, setDrawer] = useState(false);

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  };

  const contaMenu = (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          className="inline-flex min-h-[44px] items-center gap-2 rounded-pill border border-border px-3 text-sm text-text transition-colors hover:border-text"
          aria-label="Menu da conta"
        >
          <span className="grid h-6 w-6 place-items-center rounded-pill bg-accent text-xs font-semibold text-white">
            {email?.[0]?.toUpperCase() ?? "?"}
          </span>
          <span className="hidden max-w-[140px] truncate sm:inline">{email}</span>
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
  );

  return (
    <div className="flex min-h-dvh">
      {/* Sidebar fixa (desktop) */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-bg px-3 py-5 md:flex">
        <Link
          href="/feed"
          className="mb-6 inline-flex rounded-md px-2 outline-none focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Pauta"
        >
          <Logo />
        </Link>
        <SidebarLinks />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top strip */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-bg/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-bg/70">
          {/* Hambúrguer (mobile) */}
          <Dialog.Root open={drawer} onOpenChange={setDrawer}>
            <Dialog.Trigger asChild>
              <button
                className="inline-grid h-11 w-11 place-items-center rounded-md text-text md:hidden"
                aria-label="Abrir menu"
              >
                <Menu className="h-5 w-5" />
              </button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-40 bg-[#0a0e1a]/60 backdrop-blur-sm md:hidden" />
              <Dialog.Content className="fixed left-0 top-0 z-50 h-full w-[min(280px,85vw)] bg-bg p-5 shadow-[var(--shadow-2)] md:hidden">
                <div className="mb-6 flex items-center justify-between">
                  <Logo />
                  <Dialog.Close
                    aria-label="Fechar"
                    className="grid h-11 w-11 place-items-center rounded-md text-text-muted hover:text-text"
                  >
                    <X className="h-5 w-5" />
                  </Dialog.Close>
                </div>
                <Dialog.Title className="sr-only">Menu</Dialog.Title>
                <SidebarLinks onNavigate={() => setDrawer(false)} />
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>

          <div className="ml-auto flex items-center gap-2">
            <NotificationBell />
            {contaMenu}
          </div>
        </header>

        <main id="main-content" className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
