// Hosts permitidos para next/image (espelha client/next.config.ts).
// Backend pode retornar URLs de hosts não-cadastrados (dados de teste, perfis novos);
// nesses casos caímos no avatar gerado pelo ui-avatars.
const ALLOWED_FOTO_HOSTS = new Set([
  "sapl.bayeux.pb.leg.br",
  "joaopessoa.pb.leg.br",
  "ui-avatars.com",
  "www.camaracg.pb.gov.br",
  "www.santarita.pb.leg.br",
]);

export function politicoFotoSrc(p: { foto_url: string | null; nome: string }): string {
  const fallback = `https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=FF6B35&color=fff`;
  if (!p.foto_url) return fallback;
  try {
    const { hostname } = new URL(p.foto_url);
    return ALLOWED_FOTO_HOSTS.has(hostname) ? p.foto_url : fallback;
  } catch {
    return fallback;
  }
}
