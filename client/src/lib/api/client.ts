import { createClient } from "@/lib/supabase/client";
import type {
  Notificacao,
  Politico,
  PreferenciasNotificacao,
  Problema,
  ProblemaPublico,
  Recomendacao,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Anexa o access token do Supabase ao header Authorization, quando há sessão.
async function authHeaders(): Promise<Record<string, string>> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

async function handle<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`API ${resp.status}: ${detail}`);
  }
  return resp.json() as Promise<T>;
}

// Para endpoints sem corpo relevante (ações idempotentes): valida o status sem
// tentar parsear JSON, que pode vir vazio (204) e quebrar resp.json().
async function handleVoid(resp: Response): Promise<void> {
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`API ${resp.status}: ${detail}`);
  }
}

export const api = {
  // Mapa: lista problemas dentro de uma bounding box [minLng,minLat,maxLng,maxLat].
  async listarProblemas(
    bbox?: [number, number, number, number],
  ): Promise<Problema[]> {
    const qs = bbox ? `?bbox=${bbox.join(",")}` : "";
    return handle(await fetch(`${API_URL}/problemas${qs}`));
  },

  // Reportar: envia foto + coordenadas (multipart). Requer sessão.
  async criarProblema(input: {
    foto: File;
    lat: number;
    lng: number;
    descricao?: string;
  }): Promise<Problema> {
    const form = new FormData();
    form.append("foto", input.foto);
    form.append("lat", String(input.lat));
    form.append("lng", String(input.lng));
    if (input.descricao) form.append("descricao", input.descricao);
    return handle(
      await fetch(`${API_URL}/problemas`, {
        method: "POST",
        headers: await authHeaders(),
        body: form,
      }),
    );
  },

  async recomendacoes(): Promise<Recomendacao> {
    return handle(
      await fetch(`${API_URL}/recomendacoes`, { headers: await authHeaders() }),
    );
  },

  async gerarRecomendacoes(texto: string): Promise<Recomendacao> {
    return handle(
      await fetch(`${API_URL}/recomendacoes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(await authHeaders()),
        },
        body: JSON.stringify({ texto }),
      }),
    );
  },

  async listarPoliticos(opts?: {
    limite?: number;
    offset?: number;
  }): Promise<Politico[]> {
    const limite = opts?.limite ?? 50;
    const offset = opts?.offset ?? 0;
    return handle(
      await fetch(`${API_URL}/politicos?limite=${limite}&offset=${offset}`),
    );
  },

  // Seguir vereador: passa a receber alertas de `politico.atualizado`.
  // Idempotente no backend (constraint única). Requer sessão.
  async seguirPolitico(id: string): Promise<void> {
    await handleVoid(
      await fetch(`${API_URL}/politicos/${id}/seguir`, {
        method: "POST",
        headers: await authHeaders(),
      }),
    );
  },

  // Detalhe público de um problema do mapa (sem descrição/PII). Sem auth.
  async problemaPublicoPorId(id: string): Promise<ProblemaPublico> {
    return handle(await fetch(`${API_URL}/problemas/${id}`));
  },

  // Inscrever-se em um problema: recebe alertas de mudança de status. Requer sessão.
  async inscreverProblema(id: string): Promise<void> {
    await handleVoid(
      await fetch(`${API_URL}/problemas/${id}/inscrever`, {
        method: "POST",
        headers: await authHeaders(),
      }),
    );
  },

  // Define a localização base do usuário (alertas de proximidade). Requer sessão.
  async definirLocalizacao(lat: number, lng: number): Promise<void> {
    await handleVoid(
      await fetch(`${API_URL}/usuarios/me/localizacao`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(await authHeaders()),
        },
        body: JSON.stringify({ lat, lng }),
      }),
    );
  },

  async meusProblemas(opts?: {
    status?: string[];
    limite?: number;
    offset?: number;
  }): Promise<Problema[]> {
    const qs = new URLSearchParams();
    if (opts?.limite != null) qs.set("limite", String(opts.limite));
    if (opts?.offset != null) qs.set("offset", String(opts.offset));
    if (opts?.status) for (const s of opts.status) qs.append("status", s);
    return handle(
      await fetch(`${API_URL}/usuarios/me/problemas?${qs}`, {
        headers: await authHeaders(),
      }),
    );
  },

  async atualizarStatusProblema(
    id: string,
    body: { status: "resolvido" | "cancelado" },
  ): Promise<Problema> {
    return handle(
      await fetch(`${API_URL}/problemas/${id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(await authHeaders()),
        },
        body: JSON.stringify(body),
      }),
    );
  },

  async notificacoes(opts?: {
    apenasNaoLidas?: boolean;
    limite?: number;
    offset?: number;
  }): Promise<Notificacao[]> {
    const qs = new URLSearchParams();
    if (opts?.apenasNaoLidas) qs.set("apenas_nao_lidas", "true");
    if (opts?.limite != null) qs.set("limite", String(opts.limite));
    if (opts?.offset != null) qs.set("offset", String(opts.offset));
    return handle(
      await fetch(`${API_URL}/usuarios/me/notificacoes?${qs}`, {
        headers: await authHeaders(),
        cache: "no-store",
      }),
    );
  },

  async contagemNotificacoes(): Promise<{ nao_lidas: number }> {
    return handle(
      await fetch(`${API_URL}/usuarios/me/notificacoes/contagem`, {
        headers: await authHeaders(),
        cache: "no-store",
      }),
    );
  },

  async marcarNotificacaoLida(id: string): Promise<Notificacao> {
    return handle(
      await fetch(`${API_URL}/usuarios/me/notificacoes/${id}/lida`, {
        method: "PATCH",
        headers: await authHeaders(),
      }),
    );
  },

  async preferenciasNotificacao(): Promise<{
    prefs_notificacao: PreferenciasNotificacao;
  }> {
    return handle(
      await fetch(`${API_URL}/usuarios/me/notificacoes/preferencias`, {
        headers: await authHeaders(),
        cache: "no-store",
      }),
    );
  },

  async atualizarPreferenciasNotificacao(
    body: Partial<PreferenciasNotificacao>,
  ): Promise<{ prefs_notificacao: PreferenciasNotificacao }> {
    return handle(
      await fetch(`${API_URL}/usuarios/me/notificacoes`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...(await authHeaders()) },
        body: JSON.stringify(body),
      }),
    );
  },
};

export const apiBaseUrl = API_URL;
