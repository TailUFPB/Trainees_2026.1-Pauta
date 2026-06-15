"use client";

import dynamic from "next/dynamic";
import { Badge } from "@/components/primitives/Badge";
import { Card } from "@/components/primitives/Card";
import { Heading } from "@/components/primitives/Heading";
import { Skeleton } from "@/components/primitives/Skeleton";
import type { ProblemaPublico } from "@/lib/api/types";
import { statusLabel, statusTone } from "@/lib/problema-status";
import { SeguirProblemaButton } from "./SeguirProblemaButton";

// MiniMapa importado dinamicamente sem SSR — Leaflet só funciona no browser.
const MiniMapa = dynamic(
  () => import("@/components/mapa/MiniMapa").then((m) => m.MiniMapa),
  {
    ssr: false,
    loading: () => <Skeleton className="h-64 w-full rounded-md" />,
  },
);

export function ProblemaPublicoDetail({ p }: { p: ProblemaPublico }) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex flex-wrap items-center gap-3">
        <Heading level={1} size="h2" className="capitalize">
          {(p.tipo_problema ?? "outros").replace(/_/g, " ")}
        </Heading>
        <Badge tone={statusTone(p.status)}>{statusLabel(p.status)}</Badge>
        <Badge tone="accent">Severidade: {p.severidade ?? "—"}</Badge>
      </header>

      {p.foto_url ? (
        // Supabase Storage não está em remotePatterns do next.config; usamos <img>.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={p.foto_url} alt="" className="w-full rounded-md object-cover" />
      ) : null}

      {p.resumo_llm ? (
        <Card>
          <p className="text-xs uppercase tracking-wider text-text-muted">
            Resumo da IA
          </p>
          <p className="mt-2 text-sm text-text">{p.resumo_llm}</p>
        </Card>
      ) : null}

      <MiniMapa lat={p.lat} lng={p.lng} />

      <div className="flex flex-wrap items-center gap-3">
        <SeguirProblemaButton problemaId={p.id} />
        <p className="text-sm text-text-muted">
          Receba um alerta quando este problema mudar de status.
        </p>
      </div>
    </div>
  );
}
