const API_URL = "/api/backend";

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
 * Client-side: cria uma nova publicação no feed. Vai pelo proxy server-side,
 * que anexa o Bearer token a partir do cookie httpOnly. Mesmo padrão do
 * `buscarFeedClient`.
 */
export async function criarPublicacao(input: {
  conteudo: string;
  anonimo: boolean;
}): Promise<PublicacaoOut> {
  const resp = await fetch(`${API_URL}/publicacoes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? `Erro ${resp.status} ao publicar.`);
  }
  return resp.json();
}
