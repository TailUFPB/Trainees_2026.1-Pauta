import { getServerSession } from "@/lib/auth/getServerSession";
import { createClient } from "@/lib/supabase/client";

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

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface OpcoesFeed {
  cursor?: string;
  limite?: number;
}

function montarQuery(opts: OpcoesFeed): string {
  const params = new URLSearchParams();
  if (opts.cursor) params.set("cursor", opts.cursor);
  if (opts.limite) params.set("limite", String(opts.limite));
  return params.toString();
}

/**
 * Server-side: usa a sessão do cookie SSR. Tolerante a falha — devolve []
 * pra não derrubar a página inteira se o backend está fora.
 */
export async function buscarFeed(opts: OpcoesFeed = {}): Promise<ItemFeed[]> {
  try {
    const session = await getServerSession();
    const qs = montarQuery(opts);
    const resp = await fetch(`${API_URL}/feed?${qs}`, {
      headers: session
        ? { Authorization: `Bearer ${session.access_token}` }
        : {},
      cache: "no-store",
    });
    if (!resp.ok) return [];
    const data = (await resp.json()) as unknown;
    return Array.isArray(data) ? (data as ItemFeed[]) : [];
  } catch {
    return [];
  }
}

/**
 * Client-side: usado pela paginação ("Carregar mais") no FeedView.
 * Lê a sessão atual do SDK do Supabase no browser.
 */
export async function buscarFeedClient(
  opts: OpcoesFeed = {},
): Promise<ItemFeed[]> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const qs = montarQuery(opts);
  const resp = await fetch(`${API_URL}/feed?${qs}`, {
    headers: session
      ? { Authorization: `Bearer ${session.access_token}` }
      : {},
  });
  if (!resp.ok) return [];
  const data = (await resp.json()) as unknown;
  return Array.isArray(data) ? (data as ItemFeed[]) : [];
}
