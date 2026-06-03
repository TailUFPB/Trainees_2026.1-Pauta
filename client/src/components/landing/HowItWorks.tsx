import { Bell, Camera, MapPin } from "lucide-react";
import { Card } from "@/components/primitives/Card";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { FadeUp } from "@/components/motion/FadeUp";
import { StaggerChildren } from "@/components/motion/StaggerChildren";

const STEPS = [
  {
    icon: Camera,
    title: "Reporte em 30 segundos",
    body: "Foto + GPS. A IA classifica tipo e severidade automaticamente — sem formulário gigante.",
  },
  {
    icon: MapPin,
    title: "A cidade vê",
    body: "Seu problema entra no mapa público, junto com os reportes dos vizinhos. Transparência total.",
  },
  {
    icon: Bell,
    title: "Quem decide é avisado",
    body: "Vereadores e ONGs recebem alertas dos problemas da região que representam.",
  },
] as const;

export function HowItWorks() {
  return (
    <Section spacing="default">
      <Container>
        <div className="max-w-2xl">
          <FadeUp>
            <Eyebrow>Em 3 passos</Eyebrow>
          </FadeUp>
          <FadeUp delay={0.05} className="mt-4">
            <Heading level={2} size="h1">
              Reportar é mais rápido que reclamar no grupo da família.
            </Heading>
          </FadeUp>
        </div>
        <StaggerChildren className="mt-12 grid gap-5 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <FadeUp key={step.title} delay={i * 0.04}>
              <Card interactive className="h-full">
                <div className="mb-5 grid h-11 w-11 place-items-center rounded-md bg-accent/10 text-accent">
                  <step.icon className="h-5 w-5" />
                </div>
                <Heading level={3} size="h3" className="mb-2">
                  {step.title}
                </Heading>
                <p className="text-sm text-text-muted">{step.body}</p>
              </Card>
            </FadeUp>
          ))}
        </StaggerChildren>
      </Container>
    </Section>
  );
}
