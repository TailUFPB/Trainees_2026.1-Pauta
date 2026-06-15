import { MapPin } from "lucide-react";
import Link from "next/link";
import { AnonimoBadge } from "./AnonimoBadge";
import type { ItemFeed } from "@/lib/api/feed";

interface Props {
  item: ItemFeed;
}

// Card unificado do feed: lida com publicação e problema via discriminated union.
// O header (avatar/autor + timestamp) é o mesmo; o corpo varia por tipo.
export function PostCard({ item }: Props) {
  return (
    <article className="rounded-lg border border-border bg-surface p-4">
      <header className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Avatar nome={item.anonimo ? null : item.autor_nome} />
          {item.anonimo ? (
            <AnonimoBadge />
          ) : (
            <span className="text-sm font-medium text-text">
              {item.autor_nome ?? "Usuário"}
            </span>
          )}
        </div>
        <time
          dateTime={item.created_at}
          className="shrink-0 text-xs text-text-muted"
        >
          {formatarRelativo(item.created_at)}
        </time>
      </header>

      {item.tipo === "publicacao" ? (
        <ConteudoPublicacao
          texto={item.conteudo}
          imagem_url={item.imagem_url}
        />
      ) : (
        <ConteudoProblema item={item} />
      )}
    </article>
  );
}

function ConteudoPublicacao({
  texto,
  imagem_url,
}: {
  texto: string;
  imagem_url: string | null;
}) {
  return (
    <>
      <p className="whitespace-pre-wrap text-text">{texto}</p>
      {imagem_url && (
        // Supabase Storage não está em remotePatterns do next.config; usamos <img> aqui.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={imagem_url}
          alt=""
          className="mt-3 max-h-96 w-full rounded-md object-cover"
          loading="lazy"
        />
      )}
    </>
  );
}

function ConteudoProblema({
  item,
}: {
  item: Extract<ItemFeed, { tipo: "problema" }>;
}) {
  return (
    <>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-text-muted">
        <MapPin aria-hidden className="h-3 w-3" />
        <span>
          Reporte • {(item.tipo_problema ?? "outros").replace(/_/g, " ")}
          {item.severidade ? ` • ${item.severidade}` : ""}
        </span>
      </div>
      {item.resumo_llm && <p className="text-text">{item.resumo_llm}</p>}
      {item.foto_url && (
        // Supabase Storage não está em remotePatterns do next.config; usamos <img> aqui.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={item.foto_url}
          alt={item.resumo_llm ?? "Foto do reporte"}
          className="mt-3 max-h-96 w-full rounded-md object-cover"
          loading="lazy"
        />
      )}
      <Link
        href={`/problemas/${item.id}`}
        className="mt-3 inline-block text-sm font-medium text-accent hover:underline"
      >
        Ver detalhe do problema
      </Link>
    </>
  );
}

function Avatar({ nome }: { nome: string | null }) {
  const inicial = (nome ?? "?").charAt(0).toUpperCase();
  return (
    <div
      aria-hidden
      className="grid h-9 w-9 place-items-center rounded-full bg-accent/15 text-sm font-medium text-accent"
    >
      {inicial}
    </div>
  );
}

function formatarRelativo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
  return `${Math.floor(diff / 86400)} d`;
}
