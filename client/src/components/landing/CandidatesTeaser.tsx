import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { AuthGate } from "@/components/auth/AuthGate";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { FadeUp } from "@/components/motion/FadeUp";
import type { Politico } from "@/lib/api/types";
import { politicoFotoSrc } from "@/lib/politico-foto";

const FAKE_MATCH = [82, 71, 64] as const;

async function fetchTeaserPoliticos(): Promise<Politico[]> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${apiUrl}/politicos?limite=3`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return [];
    return (await res.json()) as Politico[];
  } catch {
    return [];
  }
}

export async function CandidatesTeaser() {
  const politicos = await fetchTeaserPoliticos();
  return (
    <Section spacing="default">
      <Container>
        <div className="grid items-start gap-12 md:grid-cols-2 md:gap-20">
          <div className="flex flex-col gap-6">
            <FadeUp>
              <Eyebrow>Recomendação por afinidade</Eyebrow>
            </FadeUp>
            <FadeUp delay={0.05}>
              <Heading level={2} size="h1">
                Saiba quem realmente defende suas pautas.
              </Heading>
            </FadeUp>
            <FadeUp delay={0.1}>
              <p className="max-w-md text-lg text-text-muted">
                Escreva o que importa pra você e a gente cruza com o histórico
                público dos vereadores — ranqueado por afinidade real.
              </p>
            </FadeUp>
            <FadeUp delay={0.15}>
              <AuthGate redirectTo="/candidatos/recomendacoes">
                <Button size="lg" variant="secondary" asChild>
                  <Link href="/candidatos/recomendacoes">
                    Ver minhas recomendações <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </AuthGate>
            </FadeUp>
          </div>
          <FadeUp delay={0.2} className="flex flex-col gap-3">
            {politicos.length === 0
              ? [0, 1, 2].map((i) => (
                  <Card key={i} className="flex items-center gap-4">
                    <div className="h-14 w-14 rounded-pill bg-border" />
                    <div className="flex-1 space-y-1.5">
                      <div className="h-4 w-32 rounded-sm bg-border" />
                      <div className="h-3 w-20 rounded-sm bg-border/70" />
                    </div>
                  </Card>
                ))
              : politicos.slice(0, 3).map((p, i) => (
                  <Card
                    key={p.id}
                    interactive
                    className="flex items-center gap-4"
                  >
                    <div className="relative h-14 w-14 overflow-hidden rounded-pill border border-border">
                      <Image
                        src={politicoFotoSrc(p)}
                        alt={p.nome}
                        fill
                        sizes="56px"
                        className="object-cover"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium text-text">
                        {p.nome}
                      </div>
                      <div className="truncate text-xs text-text-muted">
                        {p.cargo ?? "Vereador(a)"} · {p.municipio ?? "PB"}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-base font-semibold text-accent">
                        {FAKE_MATCH[i]}%
                      </div>
                      <div className="text-[10px] uppercase tracking-wider text-text-muted">
                        match
                      </div>
                    </div>
                  </Card>
                ))}
          </FadeUp>
        </div>
      </Container>
    </Section>
  );
}
