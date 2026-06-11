"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/conta/reportes", label: "Meus Reportes" },
  { href: "/conta/notificacoes", label: "Notificações" },
  { href: "/recomendacoes", label: "Recomendações" },
] as const;

export function AccountNav() {
  const path = usePathname();
  return (
    <nav aria-label="Navegação da conta" className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-2">
        {TABS.map((t) => {
          const active = path === t.href || path.startsWith(t.href + "/");
          return (
            <Link
              key={t.href}
              href={t.href}
              className={
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors " +
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
