// Item do feed unificado retornado por GET /feed.
// Reflete o discriminated union do backend (`tipo` separa publicação e problema).
export type ItemFeed =
  | {
      tipo: "publicacao";
      id: string;
      conteudo: string;
      imagem_url: string | null;
      anonimo: boolean;
      autor_nome: string | null;
      created_at: string;
    }
  | {
      tipo: "problema";
      id: string;
      foto_url: string | null;
      lat: number;
      lng: number;
      tipo_problema: string | null;
      severidade: string | null;
      resumo_llm: string | null;
      status: string;
      anonimo: boolean;
      autor_nome: string | null;
      created_at: string;
    };

const API_URL = "/api/backend";

/**
 * Client-side: usado pela paginação ("Carregar mais") no FeedView.
 * Vai pelo proxy server-side, que anexa o Bearer token a partir do cookie
 * httpOnly. O browser nunca lê o token.
 *
 * A versão server vive em `feed.server.ts` pra evitar arrastar `next/headers`
 * pro bundle client quando este módulo é importado por componentes "use client".
 */
export async function buscarFeedClient(
  opts: { cursor?: string; limite?: number } = {},
): Promise<ItemFeed[]> {
  const params = new URLSearchParams();
  if (opts.cursor) params.set("cursor", opts.cursor);
  if (opts.limite) params.set("limite", String(opts.limite));
  const resp = await fetch(`${API_URL}/feed?${params.toString()}`);
  if (!resp.ok) return [];
  const data = (await resp.json()) as unknown;
  return Array.isArray(data) ? (data as ItemFeed[]) : [];
}
