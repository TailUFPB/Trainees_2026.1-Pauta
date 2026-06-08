import { getServerSession } from "@/lib/auth/getServerSession";
import type { Problema } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StatsConta {
  meus_reportes: number;
  minhas_publicacoes: number;
  resolvidos: number;
}

async function serverAuthHeaders(): Promise<Record<string, string>> {
  const session = await getServerSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

// Wrapper tolerante: qualquer falha (rede, 4xx, 5xx) vira [] pra não derrubar
// o dashboard. As stats são informativas, não críticas — mas logamos pra
// debug não virar caça-fantasma (zeros no UI sem pista nos logs).
async function fetchListaTolerante<T>(path: string): Promise<T[]> {
  try {
    const headers = await serverAuthHeaders();
    const resp = await fetch(`${API_URL}${path}`, {
      headers,
      cache: "no-store",
    });
    if (!resp.ok) {
      console.error(`buscarStats falhou em ${path}: HTTP ${resp.status}`);
      return [];
    }
    const data = (await resp.json()) as unknown;
    return Array.isArray(data) ? (data as T[]) : [];
  } catch (err) {
    console.error(`buscarStats falhou em ${path}:`, err);
    return [];
  }
}

export async function buscarStats(): Promise<StatsConta> {
  const [reportes, publicacoes] = await Promise.all([
    fetchListaTolerante<Problema>("/usuarios/me/problemas?limite=100"),
    fetchListaTolerante<{ id: string }>("/usuarios/me/publicacoes?limite=100"),
  ]);
  const resolvidos = reportes.filter((r) => r.status === "resolvido").length;
  return {
    meus_reportes: reportes.length,
    minhas_publicacoes: publicacoes.length,
    resolvidos,
  };
}
