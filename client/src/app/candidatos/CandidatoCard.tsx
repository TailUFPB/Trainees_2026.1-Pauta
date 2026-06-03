import Image from "next/image";

import type { Politico } from "@/lib/api/types";

interface Props {
  politico: Politico;
}

export function CandidatoCard({ politico }: Props) {
  const conteudo = (
    <>
      {politico.foto_url ? (
        <Image
          src={politico.foto_url}
          alt={`Foto de ${politico.nome}`}
          width={300}
          height={300}
          className="aspect-square w-full rounded object-cover"
        />
      ) : (
        <div
          className="aspect-square w-full rounded bg-slate-100"
          aria-hidden
        />
      )}
      <div className="mt-3 space-y-0.5">
        <p className="text-sm font-semibold leading-snug tracking-tight text-slate-900">
          {politico.nome}
        </p>
        <p className="text-xs font-medium text-slate-500">
          {politico.partido ?? "sem partido"} · {politico.municipio ?? "—"}
        </p>
      </div>
    </>
  );

  if (politico.url_perfil) {
    return (
      <a
        href={politico.url_perfil}
        target="_blank"
        rel="noopener noreferrer"
        className="
          block cursor-pointer rounded-lg border border-slate-200 bg-white p-3
          shadow-sm transition-all duration-200 ease-out
          hover:border-slate-300 hover:shadow-md hover:-translate-y-0.5
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-600 focus-visible:ring-offset-2
        "
      >
        {conteudo}
      </a>
    );
  }

  return (
    <div className="block rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      {conteudo}
    </div>
  );
}
