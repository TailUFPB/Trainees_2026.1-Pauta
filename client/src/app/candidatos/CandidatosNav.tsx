"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { NavItem } from "@/lib/nav";

const ABAS: readonly NavItem[] = [
  { href: "/candidatos", label: "Catálogo", exact: true },
  { href: "/candidatos/recomendacoes", label: "Recomendações" },
];

// Sub-navegação em abas do hub de Candidatos. Mesmo padrão do AccountNav:
// estado ativo via pathname, aria-current e alvos de toque >=44px.
export function CandidatosNav() {
  const path = usePathname();
  return (
    <nav aria-label="Navegação de candidatos" className="border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center gap-2 overflow-x-auto px-4 py-2">
        {ABAS.map((aba) => {
          const active = aba.exact
            ? path === aba.href
            : path === aba.href || path.startsWith(aba.href + "/");
          return (
            <Link
              key={aba.href}
              href={aba.href}
              aria-current={active ? "page" : undefined}
              className={
                "inline-flex min-h-[44px] items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors " +
                (active
                  ? "bg-surface text-text"
                  : "text-text-muted hover:bg-surface hover:text-text")
              }
            >
              {aba.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
