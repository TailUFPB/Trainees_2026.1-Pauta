"use client";
import dynamic from "next/dynamic";
import { Container } from "@/components/primitives/Container";
import { Eyebrow } from "@/components/primitives/Eyebrow";
import { Heading } from "@/components/primitives/Heading";
import { Section } from "@/components/primitives/Section";
import { Skeleton } from "@/components/primitives/Skeleton";

const MapaProblemas = dynamic(
  () => import("./MapaProblemas").then((m) => m.MapaProblemas),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[60vh] w-full rounded-lg" />,
  },
);

export default function MapaPage() {
  return (
    <Section spacing="tight">
      <Container size="wide">
        <Eyebrow>Mapa da Paraíba</Eyebrow>
        <Heading level={1} size="h1" className="mt-4">
          Problemas reportados
        </Heading>
        <p className="mt-3 max-w-xl text-text-muted">
          Mova o mapa para carregar problemas da região. Cores indicam severidade.
        </p>
        <div className="mt-8 overflow-hidden rounded-lg border border-border shadow-[var(--shadow-1)]">
          <MapaProblemas />
        </div>
      </Container>
    </Section>
  );
}
