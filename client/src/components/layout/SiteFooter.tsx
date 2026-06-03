import Link from "next/link";
import { Container } from "@/components/primitives/Container";
import { ThemeToggle } from "@/components/primitives/ThemeToggle";

const CIDADES = ["João Pessoa", "Bayeux", "Santa Rita", "Campina Grande"] as const;

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-bg">
      <Container className="grid gap-10 py-12 md:grid-cols-3">
        <div className="space-y-3">
          <div className="font-display text-lg font-bold text-text">Pauta</div>
          <p className="max-w-xs text-sm text-text-muted">
            Transparência política conectada ao bem-estar das cidades — feita por
            quem mora aqui.
          </p>
        </div>
        <div className="space-y-3">
          <div className="font-mono text-xs uppercase tracking-[0.18em] text-text-muted">
            Cidades cobertas
          </div>
          <ul className="space-y-1.5 text-sm text-text">
            {CIDADES.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
        <div className="space-y-3">
          <div className="font-mono text-xs uppercase tracking-[0.18em] text-text-muted">
            Mais
          </div>
          <ul className="space-y-1.5 text-sm">
            <li>
              <Link href="/mapa" className="text-text hover:text-accent">
                Mapa de problemas
              </Link>
            </li>
            <li>
              <Link href="/recomendacoes" className="text-text hover:text-accent">
                Recomendações
              </Link>
            </li>
            <li>
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer noopener"
                className="text-text hover:text-accent"
              >
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </Container>
      <Container className="flex items-center justify-between border-t border-border py-5 text-xs text-text-muted">
        <span>© {new Date().getFullYear()} Pauta · Paraíba</span>
        <ThemeToggle />
      </Container>
    </footer>
  );
}
