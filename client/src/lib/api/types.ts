// Tipos espelhando os contratos Pydantic do backend (app/schemas).
// Mantenha em sincronia com o backend — fonte da verdade é o /openapi.json.

export type TipoProblema =
  | "buraco"
  | "alagamento"
  | "entulho"
  | "obstrucao_vegetacao"
  | "sinalizacao_defeituosa"
  | "iluminacao"
  | "calcada_irregular"
  | "outro";

export type Severidade = "baixa" | "media" | "alta" | "critica";
export type StatusProblema = "aberto" | "em_andamento" | "resolvido";

export interface Problema {
  id: string;
  autor_id: string | null;
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

export interface PoliticoMatch {
  id: string;
  nome: string;
  cargo: string | null;
  partido: string | null;
  municipio: string | null;
  resumo_llm: string | null;
  cluster_id: number | null;
  score: number | null;
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
