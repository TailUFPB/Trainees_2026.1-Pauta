import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import { NotificacoesView } from "./NotificacoesView";

export default async function NotificacoesPage() {
  const [initial, initialPrefs] = await Promise.all([
    apiServer.notificacoes({ limite: 50, offset: 0 }),
    apiServer.preferenciasNotificacao(),
  ]);

  return (
    <Section spacing="default">
      <Container size="wide">
        <Eyebrow>Sua conta</Eyebrow>
        <Heading level={1} size="h1" className="mt-2">
          Notificações
        </Heading>
        <p className="mt-3 max-w-2xl text-text-muted">
          Acompanhe atualizações importantes e controle como deseja recebê-las.
        </p>
      </Container>
      <NotificacoesView initial={initial} initialPrefs={initialPrefs} />
    </Section>
  );
}
