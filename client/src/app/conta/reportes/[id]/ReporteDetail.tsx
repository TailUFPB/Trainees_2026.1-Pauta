"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge } from "@/components/primitives/Badge";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Heading } from "@/components/primitives/Heading";
import { Skeleton } from "@/components/primitives/Skeleton";
import { api } from "@/lib/api/client";
import type { Problema } from "@/lib/api/types";

// MiniMapa importado dinamicamente sem SSR — Leaflet só funciona no browser.
const MiniMapa = dynamic(() => import("./MiniMapa").then((m) => m.MiniMapa), {
  ssr: false,
  loading: () => <Skeleton className="h-64 w-full rounded-md" />,
});

// Tom visual do badge de status. Reaproveita o mesmo mapeamento usado em
// `ReporteCard`, cobrindo todos os 5 status possíveis (ver migrations 0006/0007).
const STATUS_TONE: Record<string, "neutral" | "accent" | "success" | "danger"> = {
  aberto: "accent",
  em_andamento: "neutral",
  resolvido: "success",
  arquivado: "neutral",
  cancelado: "danger",
};

const STATUS_LABEL: Record<string, string> = {
  aberto: "Aberto",
  em_andamento: "Em andamento",
  resolvido: "Resolvido",
  arquivado: "Arquivado",
  cancelado: "Cancelado",
};

export function ReporteDetail({ p: inicial }: { p: Problema }) {
  const [p, setP] = useState(inicial);
  const [pending, setPending] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();

  // Só permitimos resolver/cancelar enquanto o reporte ainda está ativo.
  const podeAgir = p.status === "aberto" || p.status === "em_andamento";

  async function agir(status: "resolvido" | "cancelado") {
    setPending(true);
    setErro(null);
    try {
      const atualizado = await api.atualizarStatusProblema(p.id, { status });
      setP(atualizado);
      router.refresh();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao atualizar o reporte.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-wrap items-center gap-3">
        <Heading level={1} size="h2" className="capitalize">
          {(p.tipo_problema ?? "outros").replace(/_/g, " ")}
        </Heading>
        <Badge tone={STATUS_TONE[p.status] ?? "neutral"}>
          {STATUS_LABEL[p.status] ?? p.status}
        </Badge>
        <Badge tone="accent">Severidade: {p.severidade ?? "—"}</Badge>
        <Badge>
          Confiança:{" "}
          {p.confianca != null ? `${(p.confianca * 100).toFixed(0)}%` : "—"}
        </Badge>
      </header>

      {p.foto_url ? (
        // Supabase Storage não está em remotePatterns do next.config; usamos <img>.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={p.foto_url}
          alt=""
          className="w-full rounded-md object-cover"
        />
      ) : null}

      {p.descricao ? (
        <Card>
          <p className="text-sm text-text">{p.descricao}</p>
        </Card>
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

      {podeAgir ? (
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => agir("resolvido")} loading={pending}>
            Marcar como resolvido
          </Button>
          <Button
            variant="secondary"
            onClick={() => agir("cancelado")}
            loading={pending}
          >
            Cancelar reporte
          </Button>
        </div>
      ) : null}

      {erro ? (
        <div
          role="alert"
          className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
        >
          {erro}
        </div>
      ) : null}
    </div>
  );
}
