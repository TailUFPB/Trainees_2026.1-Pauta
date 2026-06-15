// Tipos espelhando os contratos Pydantic do backend (app/schemas).
// Mantenha em sincronia com o backend — fonte da verdade é o /openapi.json.

export type TipoProblema =
  | "asfalto"
  | "alagamento"
  | "iluminacao"
  | "lixo"
  | "arborizacao"
  | "sinalizacao"
  | "calcada"
  | "esgoto"
  | "outros"
  | "nenhum";

export type Severidade = "baixa" | "media" | "alta" | "critica";
export type StatusProblema = "aberto" | "em_andamento" | "resolvido";

export interface Problema {
  id: string;
  foto_url: string | null;
  lat: number;
  lng: number;
  tipo_problema: TipoProblema | null;
  severidade: Severidade | null;
  resumo_llm: string | null;
  palavras_chave: string[];
  confianca: number | null;
  modelo_utilizado: string | null;
  precisa_revisao: boolean;
  status: StatusProblema;
  resolvido_por: string | null;
  resolvido_em: string | null;
  descricao: string | null;
  created_at: string;
}

/** Versão pública de um problema — sem autor_id e descricao. */
export type ProblemaPublico = Omit<Problema, "autor_id" | "descricao">;

export interface PoliticoMatch {
  id: string;
  nome: string;
  cargo: string | null;
  partido: string | null;
  municipio: string | null;
  resumo_llm: string | null;
  cluster_id: number | null;
  score: number | null;
  justificativa: string | null;
  evidencias: EvidenciaProposta[];
}

export interface EvidenciaProposta {
  tipo: string | null;
  numero: number | null;
  ano: number | null;
  resumo: string;
}

export interface Recomendacao {
  placeholder: boolean;
  top_politicos: PoliticoMatch[];
  cluster_alinhado: number | null;
}

export interface Politico {
  id: string;
  nome: string;
  cargo: string | null;
  partido: string | null;
  municipio: string | null;
  foto_url: string | null;
  url_perfil: string | null;
  cluster_id: number | null;
}

export interface Notificacao {
  id: string;
  tipo: string;
  titulo: string;
  mensagem: string;
  link_destino: string | null;
  lida: boolean;
  canais: Record<string, string>;
  dados: Record<string, unknown>;
  created_at: string;
  lida_em: string | null;
}

export interface PreferenciasNotificacao {
  interna: boolean;
  email: boolean;
  push: boolean;
  problemas_perto: boolean;
  politicos: boolean;
  resumo_semanal: boolean;
  token_fcm?: string;
}
