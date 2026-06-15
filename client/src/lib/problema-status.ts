// Mapeamento único de status do problema → tom/rótulo do Badge. Antes estava
// duplicado em ReporteCard e ReporteDetail; centralizado aqui para o catálogo,
// o detalhe do autor e o detalhe público ficarem sempre coerentes.
import type { StatusProblema } from "@/lib/api/types";

export type BadgeTone = "neutral" | "accent" | "success" | "danger";

export const STATUS_TONE: Record<string, BadgeTone> = {
  aberto: "accent",
  em_andamento: "neutral",
  resolvido: "success",
  arquivado: "neutral",
  cancelado: "danger",
};

export const STATUS_LABEL: Record<string, string> = {
  aberto: "Aberto",
  em_andamento: "Em andamento",
  resolvido: "Resolvido",
  arquivado: "Arquivado",
  cancelado: "Cancelado",
};

export function statusTone(status: StatusProblema | string): BadgeTone {
  return STATUS_TONE[status] ?? "neutral";
}

export function statusLabel(status: StatusProblema | string): string {
  return STATUS_LABEL[status] ?? status;
}
