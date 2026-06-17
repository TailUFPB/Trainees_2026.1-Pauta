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
 *
 * Multipart: a `foto` (opcional) é enviada como arquivo; o backend valida,
 * sobe pro storage e devolve a URL pública em `imagem_url`. Não setar
 * Content-Type — o browser define o boundary do multipart automaticamente.
 */
export async function criarPublicacao(input: {
  conteudo: string;
  anonimo: boolean;
  foto?: File | null;
}): Promise<PublicacaoOut> {
  const form = new FormData();
  form.set("conteudo", input.conteudo);
  form.set("anonimo", String(input.anonimo));
  if (input.foto) form.set("foto", input.foto);

  const resp = await fetch(`${API_URL}/publicacoes`, {
    method: "POST",
    body: form,
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? `Erro ${resp.status} ao publicar.`);
  }
  return resp.json();
}
