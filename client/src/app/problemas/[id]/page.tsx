import { notFound } from "next/navigation";
import { Container } from "@/components/primitives/Container";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import type { ProblemaPublico } from "@/lib/api/types";
import { ProblemaPublicoDetail } from "./ProblemaPublicoDetail";

// Página pública de detalhe de um problema do mapa/feed. Usa a versão sem PII
// (GET /problemas/{id}). Qualquer um pode ver; seguir exige login (no botão).
export default async function ProblemaPublicoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let problema: ProblemaPublico;
  try {
    problema = await apiServer.problemaPublicoPorId(id);
  } catch {
    notFound();
  }

  return (
    <Section spacing="default">
      <Container size="wide">
        <ProblemaPublicoDetail p={problema} />
      </Container>
    </Section>
  );
}
