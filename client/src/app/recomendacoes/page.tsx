"use client";
import { useEffect, useState, type FormEvent } from "react";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { Skeleton } from "@/components/primitives/Skeleton";
import { api } from "@/lib/api/client";
import type { Recomendacao } from "@/lib/api/types";
import { useSession } from "@/lib/hooks/useSession";
import { useLoginModal } from "@/components/auth/LoginModalProvider";

export default function RecomendacoesPage() {
  const { user, loading: sessionLoading } = useSession();
  const { open } = useLoginModal();
  const [texto, setTexto] = useState("");
  const [data, setData] = useState<Recomendacao | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api
      .recomendacoes()
      .then(setData)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Erro ao carregar."),
      )
      .finally(() => setLoading(false));
  }, [user]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) {
      open("/recomendacoes");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.definirInteresses(texto);
      const r = await api.recomendacoes();
      setData(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Section spacing="default">
      <Container size="narrow">
        <Eyebrow>Recomendação por afinidade</Eyebrow>
        <Heading level={1} size="h1" className="mt-4">
          Conte suas pautas. Cruzamos com a Câmara.
        </Heading>
        <p className="mt-4 text-text-muted">
          Escreva os temas que importam pra você — saneamento, mobilidade,
          mulheres, educação. A gente ranqueia os vereadores com posicionamento
          mais próximo.
        </p>

        {sessionLoading ? null : !user ? (
          <Card className="mt-8 flex flex-col gap-3 text-center">
            <p className="text-text-muted">
              Pra ver suas recomendações, entre na sua conta.
            </p>
            <Button onClick={() => open("/recomendacoes")}>Entrar</Button>
          </Card>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
            <label className="flex flex-col gap-2 text-sm font-medium text-text">
              Suas pautas
              <textarea
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                rows={5}
                placeholder="Ex: melhor transporte público no bairro, proteção a ciclistas, mais creches na zona sul…"
                className="w-full rounded-md border border-border bg-surface p-4 text-base text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </label>
            <Button
              type="submit"
              size="lg"
              loading={loading}
              disabled={!texto.trim()}
            >
              <Sparkles className="h-4 w-4" />
              Gerar recomendações
            </Button>
          </form>
        )}

        {error ? (
          <div
            role="alert"
            className="mt-6 rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            {error}
          </div>
        ) : null}

        {loading && !data ? (
          <div className="mt-10 space-y-3">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        ) : data && data.top_politicos.length > 0 ? (
          <div className="mt-10 space-y-3">
            <Eyebrow tone="muted">Top matches</Eyebrow>
            {data.top_politicos.map((m, i) => (
              <Card key={m.id} className="flex items-center gap-4">
                <div className="grid h-10 w-10 place-items-center rounded-pill bg-accent/10 font-mono text-sm font-semibold text-accent">
                  {i + 1}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-text">{m.nome}</div>
                  <div className="truncate text-xs text-text-muted">
                    {m.cargo ?? "Vereador(a)"} ·{" "}
                    {m.partido ? `${m.partido} · ` : ""}
                    {m.municipio ?? "PB"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-lg font-semibold text-text">
                    {((m.score ?? 0) * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-text-muted">
                    afinidade
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : null}
      </Container>
    </Section>
  );
}
