import { createClient } from "@/lib/supabase/client";
import type { Politico, Problema, Recomendacao } from "./types";

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

export const api = {
  // Mapa: lista problemas dentro de uma bounding box [minLng,minLat,maxLng,maxLat].
  async listarProblemas(bbox?: [number, number, number, number]): Promise<Problema[]> {
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

  async listarPoliticos(opts?: { limite?: number; offset?: number }): Promise<Politico[]> {
    const limite = opts?.limite ?? 50;
    const offset = opts?.offset ?? 0;
    return handle(
      await fetch(`${API_URL}/politicos?limite=${limite}&offset=${offset}`),
    );
  },

  async definirInteresses(texto: string): Promise<unknown> {
    return handle(
      await fetch(`${API_URL}/usuarios/me/interesses`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(await authHeaders()) },
        body: JSON.stringify({ texto }),
      }),
    );
  },
};

export const apiBaseUrl = API_URL;
