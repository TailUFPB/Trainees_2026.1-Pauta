"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  exact?: boolean;
}

const ITENS: readonly NavItem[] = [
  { href: "/conta", label: "Dashboard", exact: true },
  { href: "/conta/feed", label: "Feed" },
  { href: "/conta/reportes", label: "Minha pauta" },
  { href: "/conta/notificacoes", label: "Notificações" },
  { href: "/recomendacoes", label: "Recomendações" },
];

export function AccountNav() {
  const path = usePathname();
  return (
    <nav aria-label="Navegação da conta" className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center gap-2 overflow-x-auto px-4 py-2">
        {ITENS.map((t) => {
          // Para "/conta" usamos igualdade estrita; do contrário "/conta/feed"
          // marcaria Dashboard como ativo também.
          const active = t.exact
            ? path === t.href
            : path === t.href || path.startsWith(t.href + "/");
          return (
            <Link
              key={t.href}
              href={t.href}
              aria-current={active ? "page" : undefined}
              className={
                "inline-flex min-h-[44px] items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors " +
                (active
                  ? "bg-surface text-text"
                  : "text-text-muted hover:bg-surface hover:text-text")
              }
            >
              {t.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
