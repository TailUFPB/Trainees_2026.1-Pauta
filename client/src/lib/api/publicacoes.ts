import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Resposta do POST /publicacoes — espelha PublicacaoOut do backend.
export interface PublicacaoOut {
  id: string;
  conteudo: string;
  imagem_url: string | null;
  anonimo: boolean;
  autor_nome: string | null;
  created_at: string;
}

/**
 * Client-side: cria uma nova publicação no feed. Usa o JWT da sessão atual
 * do Supabase no browser, mesmo padrão do `buscarFeedClient`.
 */
export async function criarPublicacao(input: {
  conteudo: string;
  anonimo: boolean;
}): Promise<PublicacaoOut> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const resp = await fetch(`${API_URL}/publicacoes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.access_token ?? ""}`,
    },
    body: JSON.stringify(input),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? `Erro ${resp.status} ao publicar.`);
  }
  return resp.json();
}
