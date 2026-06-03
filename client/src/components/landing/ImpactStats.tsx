import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { FadeUp } from "@/components/motion/FadeUp";
import { CountUp } from "@/components/motion/CountUp";

interface Problema {
  status: string;
}

async function fetchStats() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${apiUrl}/problemas`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) throw new Error("API off");
    const problemas: Problema[] = await res.json();
    const total = problemas.length;
    const resolvidos = problemas.filter((p) => p.status === "resolvido").length;
    return { total, resolvidos, cidades: 4 };
  } catch {
    return { total: 0, resolvidos: 0, cidades: 4 };
  }
}

export async function ImpactStats() {
  const { total, resolvidos, cidades } = await fetchStats();
  return (
    <Section tone="muted" spacing="default">
      <Container>
        <div className="max-w-2xl">
          <FadeUp>
            <Eyebrow>Por enquanto</Eyebrow>
          </FadeUp>
          <FadeUp delay={0.05} className="mt-4">
            <Heading level={2} size="h1">
              Já estamos cobrindo:
            </Heading>
          </FadeUp>
        </div>
        <div className="mt-12 grid gap-12 md:grid-cols-3 md:gap-8">
          <FadeUp>
            <div className="border-l-2 border-accent pl-6 md:pl-8">
              <div className="font-mono text-[length:clamp(3rem,2rem+4vw,4.5rem)] font-semibold tabular-nums leading-none text-text">
                <CountUp to={total} />
              </div>
              <div className="mt-3 text-sm text-text-muted">
                problemas reportados
              </div>
            </div>
          </FadeUp>
          <FadeUp delay={0.05}>
            <div className="border-l-2 border-success pl-6 md:pl-8">
              <div className="font-mono text-[length:clamp(3rem,2rem+4vw,4.5rem)] font-semibold tabular-nums leading-none text-text">
                <CountUp to={resolvidos} />
              </div>
              <div className="mt-3 text-sm text-text-muted">resolvidos</div>
            </div>
          </FadeUp>
          <FadeUp delay={0.1}>
            <div className="border-l-2 border-info pl-6 md:pl-8">
              <div className="font-mono text-[length:clamp(3rem,2rem+4vw,4.5rem)] font-semibold tabular-nums leading-none text-text">
                <CountUp to={cidades} />
              </div>
              <div className="mt-3 text-sm text-text-muted">cidades cobertas</div>
            </div>
          </FadeUp>
        </div>
      </Container>
    </Section>
  );
}
