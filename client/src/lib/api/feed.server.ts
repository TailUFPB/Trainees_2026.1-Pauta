import { getServerSession } from "@/lib/auth/getServerSession";
import type { ItemFeed } from "./feed";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Server-side: usa a sessão do cookie SSR. Tolerante a falha — devolve []
 * pra não derrubar a página inteira se o backend está fora.
 *
 * Vive em arquivo separado de `feed.ts` pra não arrastar `next/headers`
 * (importado por `getServerSession`) pro bundle client.
 */
export async function buscarFeed(
  opts: { cursor?: string; limite?: number } = {},
): Promise<ItemFeed[]> {
  try {
    const session = await getServerSession();
    const params = new URLSearchParams();
    if (opts.cursor) params.set("cursor", opts.cursor);
    if (opts.limite) params.set("limite", String(opts.limite));
    const resp = await fetch(`${API_URL}/feed?${params.toString()}`, {
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
