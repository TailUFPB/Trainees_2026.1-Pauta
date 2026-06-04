"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/primitives/Button";
import { api } from "@/lib/api/client";
import type { Problema } from "@/lib/api/types";
import { EmptyState } from "./EmptyState";
import { ReporteCard } from "./ReporteCard";

// Opções de filtro multi-seleção. Mantemos `arquivado` e `cancelado` porque o
// banco já aceita esses valores (migrations 0006/0007), mesmo que o enum de
// status do TS ainda esteja restrito aos três originais.
const STATUS_OPCOES = [
  { value: "aberto", label: "Aberto" },
  { value: "em_andamento", label: "Em andamento" },
  { value: "resolvido", label: "Resolvido" },
  { value: "arquivado", label: "Arquivado" },
  { value: "cancelado", label: "Cancelado" },
];

const PAGE = 20;

export function MeusReportesView({ initial }: { initial: Problema[] }) {
  const [items, setItems] = useState(initial);
  const [esgotou, setEsgotou] = useState(initial.length < PAGE);
  const [status, setStatus] = useState<string[]>([]);
  const [pending, start] = useTransition();

  function aplicarFiltro(novo: string[]) {
    setStatus(novo);
    start(async () => {
      const novos = await api.meusProblemas({
        status: novo,
        limite: PAGE,
        offset: 0,
      });
      setItems(novos);
      setEsgotou(novos.length < PAGE);
    });
  }

  function carregarMais() {
    start(async () => {
      const novos = await api.meusProblemas({
        status,
        limite: PAGE,
        offset: items.length,
      });
      setItems((a) => [...a, ...novos]);
      if (novos.length < PAGE) setEsgotou(true);
    });
  }

  // Empty state real: nenhum problema e nenhum filtro aplicado.
  // Se houver filtro ativo, mostramos a mensagem "nenhum reporte com esse filtro"
  // mais embaixo, mantendo os botões de filtro pra o usuário ajustar.
  if (items.length === 0 && status.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-4 flex flex-wrap gap-2">
        {STATUS_OPCOES.map((o) => {
          const active = status.includes(o.value);
          return (
            <button
              key={o.value}
              type="button"
              onClick={() =>
                aplicarFiltro(
                  active
                    ? status.filter((s) => s !== o.value)
                    : [...status, o.value],
                )
              }
              className={
                "rounded-pill border px-3 py-1 text-xs font-medium transition-colors " +
                (active
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-border text-text-muted hover:border-text")
              }
            >
              {o.label}
            </button>
          );
        })}
      </div>

      {items.length === 0 ? (
        <p className="py-10 text-center text-text-muted">
          Nenhum reporte com esse filtro.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((p) => (
            <ReporteCard key={p.id} p={p} />
          ))}
        </div>
      )}

      {!esgotou && items.length > 0 ? (
        <div className="mt-6 flex justify-center">
          <Button
            variant="secondary"
            onClick={carregarMais}
            loading={pending}
          >
            Carregar mais
          </Button>
        </div>
      ) : null}
    </div>
  );
}
