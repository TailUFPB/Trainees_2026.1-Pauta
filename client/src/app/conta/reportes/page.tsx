import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import { MeusReportesView } from "./MeusReportesView";

// Página server-side: busca a primeira página de "meus problemas" no servidor
// pra evitar flash de loading e delegar a interatividade (filtros + paginação)
// pro componente client `MeusReportesView`.
export default async function MeusReportesPage() {
  const initial = await apiServer.meusProblemas({ limite: 20, offset: 0 });

  return (
    <Section spacing="default">
      <Container size="wide">
        <Eyebrow>Sua conta</Eyebrow>
        <Heading level={1} size="h1" className="mt-2">
          Meus Reportes
        </Heading>
      </Container>
      <MeusReportesView initial={initial} />
    </Section>
  );
}
