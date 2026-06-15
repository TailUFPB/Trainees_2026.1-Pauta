import Link from "next/link";
import { Button } from "@/components/primitives/Button";
import { Container } from "@/components/primitives/Container";
import { getServerUser } from "@/lib/auth/getServerSession";
import { buscarStats } from "@/lib/api/stats";

// Server component: saúda o usuário, mostra um resumo da atividade e
// expõe atalhos para as principais ações da conta.
export default async function DashboardPage() {
  const user = await getServerUser();
  const nome =
    (user?.user_metadata?.name as string | undefined)?.split(" ")[0] ??
    user?.email?.split("@")[0] ??
    "cidadão";

  const stats = await buscarStats();

  return (
    <Container className="py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-text">
          Olá, {nome}.
        </h1>
        <p className="mt-1 text-text-muted">
          Veja o que está acontecendo na sua pauta hoje.
        </p>
      </header>

      <section aria-label="Resumo" className="mb-10 grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Meus reportes"
          valor={stats.meus_reportes}
          href="/conta/reportes"
        />
        <StatCard
          label="Minhas publicações"
          valor={stats.minhas_publicacoes}
          href="/feed"
        />
        <StatCard label="Resolvidos" valor={stats.resolvidos} />
      </section>

      <section aria-labelledby="acoes">
        <h2 id="acoes" className="mb-4 text-lg font-semibold text-text">
          Ações
        </h2>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild variant="primary">
            <Link href="/reportar">Reportar problema</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link href="/feed">Ver feed</Link>
          </Button>
        </div>
      </section>
    </Container>
  );
}

function StatCard({
  label,
  valor,
  href,
}: {
  label: string;
  valor: number;
  href?: string;
}) {
  const inner = (
    <div className="rounded-lg border border-border bg-surface p-5 transition hover:border-accent/40">
      <div className="text-3xl font-semibold tabular-nums text-text">
        {valor}
      </div>
      <div className="mt-1 text-sm text-text-muted">{label}</div>
    </div>
  );
  return href ? (
    <Link
      href={href}
      className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg rounded-lg"
    >
      {inner}
    </Link>
  ) : (
    inner
  );
}
