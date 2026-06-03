import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { Badge } from "@/components/primitives/Badge";
import { api } from "@/lib/api/client";
import { CandidatoCard } from "./CandidatoCard";

export default async function CandidatosPage() {
  let politicos;
  let error: string | null = null;
  try {
    politicos = await api.listarPoliticos();
  } catch (err) {
    error = err instanceof Error ? err.message : "Erro ao carregar candidatos.";
    politicos = [];
  }

  return (
    <Section spacing="default">
      <Container>
        <div className="flex items-end justify-between gap-4">
          <div>
            <Eyebrow>Catálogo</Eyebrow>
            <Heading level={1} size="h1" className="mt-4">
              Vereadores monitorados
            </Heading>
          </div>
          <Badge>{politicos.length} pessoas</Badge>
        </div>

        {error ? (
          <div
            role="alert"
            className="mt-10 rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            {error}
          </div>
        ) : (
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {politicos.map((p) => (
              <CandidatoCard key={p.id} politico={p} />
            ))}
          </div>
        )}
      </Container>
    </Section>
  );
}
