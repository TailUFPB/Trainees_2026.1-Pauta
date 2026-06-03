import { api } from "@/lib/api/client";

import { CandidatoCard } from "./CandidatoCard";

export const dynamic = "force-dynamic";

export default async function CandidatosPage() {
  let politicos;
  try {
    politicos = await api.listarPoliticos();
  } catch (err) {
    console.error("Erro ao carregar candidatos:", err);
    return (
      <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
        <header className="mb-8 border-l-4 border-green-600 pl-4">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Candidatos
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Catálogo de representantes políticos
          </p>
        </header>

        <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center">
          <p className="text-sm font-semibold text-red-700">
            Não foi possível carregar os candidatos.
          </p>
          <p className="mt-1 text-xs text-red-500">
            Tente novamente em alguns instantes.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
      <header className="mb-2 flex items-start justify-between border-l-4 border-green-600 pl-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Candidatos
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Catálogo de representantes políticos
          </p>
        </div>
        <span className="mt-1 shrink-0 rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold tabular-nums text-slate-700">
          {politicos.length}
        </span>
      </header>

      <div className="mb-8 border-b border-slate-100" />

      {politicos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <p className="text-lg font-semibold text-slate-700">
            Nenhum candidato encontrado
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Os dados do catálogo ainda não foram carregados.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {politicos.map((p) => (
            <CandidatoCard key={p.id} politico={p} />
          ))}
        </div>
      )}
    </main>
  );
}
