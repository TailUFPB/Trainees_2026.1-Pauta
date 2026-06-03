import { getServerSession } from "@/lib/auth/getServerSession";
import type { Problema, ProblemaPublico } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function serverAuthHeaders(): Promise<Record<string, string>> {
  const session = await getServerSession();
  return session ? { Authorization: `Bearer ${session.access_token}` } : {};
}

async function handle<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const detail = await resp.text();
    throw new Error(`API ${resp.status}: ${detail}`);
  }
  return resp.json() as Promise<T>;
}

export const apiServer = {
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
        headers: await serverAuthHeaders(),
        cache: "no-store",
      }),
    );
  },

  async problemaPorIdComoAutor(id: string): Promise<Problema | ProblemaPublico> {
    return handle(
      await fetch(`${API_URL}/problemas/${id}`, {
        headers: await serverAuthHeaders(),
        cache: "no-store",
      }),
    );
  },
};
