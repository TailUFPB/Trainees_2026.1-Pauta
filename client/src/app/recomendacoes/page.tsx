"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { Recomendacao } from "@/lib/api/types";

export default function RecomendacoesPage() {
  const [texto, setTexto] = useState("");
  const [rec, setRec] = useState<Recomendacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function carregar() {
    setErro(null);
    try {
      setRec(await api.recomendacoes());
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar.");
    }
  }

  useEffect(() => {
    api
      .recomendacoes()
      .then((r) => setRec(r))
      .catch((e) => setErro(e instanceof Error ? e.message : "Falha ao carregar."));
  }, []);

  async function salvarInteresses(e: React.FormEvent) {
    e.preventDefault();
    setCarregando(true);
    setErro(null);
    try {
      await api.definirInteresses(texto);
      await carregar();
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Falha ao salvar interesses.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold tracking-tight">Candidatos para você</h1>
      <p className="mt-1 text-sm text-zinc-600">
        Descreva as pautas que mais te importam. A recomendação usa similaridade entre o seu
        perfil e o dos políticos.
      </p>

      <form onSubmit={salvarInteresses} className="mt-5 flex flex-col gap-3">
        <textarea
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="ex.: saúde pública, mobilidade urbana, educação infantil…"
          rows={3}
          className="rounded border border-zinc-300 p-2"
        />
        <button
          type="submit"
          disabled={carregando || texto.trim().length === 0}
          className="self-start rounded bg-zinc-900 px-4 py-2 text-white disabled:opacity-50"
        >
          {carregando ? "Salvando…" : "Atualizar meus interesses"}
        </button>
      </form>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}

      <div className="mt-6">
        {rec?.placeholder && (
          <p className="rounded border border-amber-200 bg-amber-50 p-3 text-sm">
            Ainda não há recomendações. Defina seus interesses acima — e os perfis dos políticos
            precisam estar carregados pelo pipeline de dados.
          </p>
        )}

        {rec && !rec.placeholder && (
          <ul className="flex flex-col gap-2">
            {rec.top_politicos.map((p) => (
              <li key={p.id} className="rounded border border-zinc-200 bg-white p-4">
                <div className="flex items-baseline justify-between">
                  <span className="font-medium">{p.nome}</span>
                  {p.score != null && (
                    <span className="text-sm text-emerald-700">
                      {Math.round(p.score * 100)}% afinidade
                    </span>
                  )}
                </div>
                <p className="text-sm text-zinc-600">
                  {[p.cargo, p.partido, p.municipio].filter(Boolean).join(" · ")}
                </p>
                {p.resumo_llm && <p className="mt-1 text-sm text-zinc-600">{p.resumo_llm}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
