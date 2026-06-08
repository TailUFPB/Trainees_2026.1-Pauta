"use client";

import { useState } from "react";

import { api } from "@/lib/api/client";
import type { Politico } from "@/lib/api/types";

import { CandidatoCard } from "./CandidatoCard";

const PAGE_SIZE = 50;

interface Props {
  initial: Politico[];
}

export function CandidatosGrid({ initial }: Props) {
  const [politicos, setPoliticos] = useState<Politico[]>(initial);
  const [carregando, setCarregando] = useState(false);
  const [esgotou, setEsgotou] = useState(initial.length < PAGE_SIZE);
  const [erro, setErro] = useState<string | null>(null);

  async function carregarMais() {
    setCarregando(true);
    setErro(null);
    try {
      const novos = await api.listarPoliticos({
        limite: PAGE_SIZE,
        offset: politicos.length,
      });
      setPoliticos((atual) => [...atual, ...novos]);
      if (novos.length < PAGE_SIZE) setEsgotou(true);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro ao carregar mais candidatos.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {politicos.map((p) => (
          <CandidatoCard key={p.id} politico={p} />
        ))}
      </div>
      {erro ? (
        <div
          role="alert"
          className="mt-6 rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
        >
          {erro}
        </div>
      ) : null}
      {!esgotou ? (
        <div className="mt-8 flex justify-center">
          <button
            type="button"
            onClick={carregarMais}
            disabled={carregando}
            className="rounded-md border border-border bg-surface px-4 py-2 text-sm font-medium text-text transition hover:bg-surface-hover disabled:opacity-50"
          >
            {carregando ? "Carregando..." : "Carregar mais"}
          </button>
        </div>
      ) : null}
    </>
  );
}
