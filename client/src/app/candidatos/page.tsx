import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { Badge } from "@/components/primitives/Badge";
import { apiServer } from "@/lib/api/serverClient";
import type { Politico } from "@/lib/api/types";

import { CandidatosGrid } from "./CandidatosGrid";

const PAGE_SIZE = 50;

export default async function CandidatosPage() {
  let politicos: Politico[] = [];
  let error: string | null = null;
  try {
    politicos = await apiServer.listarPoliticos({ limite: PAGE_SIZE, offset: 0 });
  } catch (err) {
    error = err instanceof Error ? err.message : "Erro ao carregar candidatos.";
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
          <Badge>{politicos.length}+ pessoas</Badge>
        </div>

        {error ? (
          <div
            role="alert"
            className="mt-10 rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
          >
            {error}
          </div>
        ) : (
          <CandidatosGrid initial={politicos} />
        )}
      </Container>
    </Section>
  );
}
