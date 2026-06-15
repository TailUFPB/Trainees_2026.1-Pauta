import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { apiServer } from "@/lib/api/serverClient";
import { ConfiguracoesView } from "./ConfiguracoesView";

// Configurações da conta: preferências de notificação (canais) + localização
// base para alertas de proximidade. A central de notificações fica separada,
// como caixa de entrada pura, em /conta/notificacoes.
export default async function ConfiguracoesPage() {
  const prefs = await apiServer.preferenciasNotificacao();

  return (
    <Section spacing="default">
      <Container size="wide">
        <Eyebrow>Sua conta</Eyebrow>
        <Heading level={1} size="h1" className="mb-8 mt-2">
          Configurações
        </Heading>
      </Container>
      <ConfiguracoesView initialPrefs={prefs} />
    </Section>
  );
}
