"use client";

import { useState } from "react";
import { api } from "@/lib/api/client";
import type { Problema } from "@/lib/api/types";

export default function ReportarPage() {
  const [foto, setFoto] = useState<File | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [descricao, setDescricao] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Problema | null>(null);

  function pegarLocalizacao() {
    setErro(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setErro("Não foi possível obter sua localização."),
    );
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setResultado(null);
    if (!foto || !coords) {
      setErro("Selecione uma foto e informe a localização.");
      return;
    }
    setEnviando(true);
    try {
      const p = await api.criarProblema({ foto, ...coords, descricao });
      setResultado(p);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha ao enviar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold tracking-tight">Reportar problema</h1>
      <p className="mt-1 text-sm text-zinc-600">Requer estar logado.</p>

      <form onSubmit={enviar} className="mt-5 flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Foto
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => setFoto(e.target.files?.[0] ?? null)}
            className="rounded border border-zinc-300 p-2"
          />
        </label>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={pegarLocalizacao}
            className="rounded border border-zinc-300 px-3 py-2 text-sm"
          >
            Usar minha localização
          </button>
          {coords && (
            <span className="text-xs text-zinc-500">
              {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
            </span>
          )}
        </div>

        <label className="flex flex-col gap-1 text-sm">
          Descrição (opcional)
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            className="rounded border border-zinc-300 p-2"
            rows={3}
          />
        </label>

        <button
          type="submit"
          disabled={enviando}
          className="rounded bg-zinc-900 px-4 py-2 text-white disabled:opacity-50"
        >
          {enviando ? "Enviando…" : "Enviar"}
        </button>
      </form>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}

      {resultado && (
        <div className="mt-5 rounded border border-emerald-200 bg-emerald-50 p-4 text-sm">
          <p className="font-medium">Problema registrado!</p>
          <p>
            Tipo: <strong>{resultado.tipo_problema}</strong> · Severidade:{" "}
            <strong>{resultado.severidade}</strong> · Confiança:{" "}
            {resultado.confianca?.toFixed(2)}
          </p>
          {resultado.precisa_revisao && <p>⚠️ Marcado para revisão humana (baixa confiança).</p>}
          <p className="mt-1 text-zinc-600">{resultado.resumo_llm}</p>
        </div>
      )}
    </div>
  );
}
