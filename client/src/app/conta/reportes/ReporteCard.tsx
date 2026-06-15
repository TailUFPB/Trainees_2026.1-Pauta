import Link from "next/link";
import { Badge } from "@/components/primitives/Badge";
import { Card } from "@/components/primitives/Card";
import type { Problema } from "@/lib/api/types";

// Mapeia status do problema para o tom visual do Badge.
// Cobre todos os 5 status possíveis (ver migrations 0006/0007).
const STATUS_TONE: Record<string, "neutral" | "accent" | "success" | "danger"> = {
  aberto: "accent",
  em_andamento: "neutral",
  resolvido: "success",
  arquivado: "neutral",
  cancelado: "danger",
};

const STATUS_LABEL: Record<string, string> = {
  aberto: "Aberto",
  em_andamento: "Em andamento",
  resolvido: "Resolvido",
  arquivado: "Arquivado",
  cancelado: "Cancelado",
};

export function ReporteCard({ p }: { p: Problema }) {
  const data = new Date(p.created_at).toLocaleDateString("pt-BR");
  return (
    <Link href={`/conta/reportes/${p.id}`} className="block">
      <Card className="flex items-center gap-4 transition-shadow hover:shadow-[var(--shadow-2)]">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium capitalize text-text">
              {(p.tipo_problema ?? "outros").replace(/_/g, " ")}
            </span>
            <Badge tone={STATUS_TONE[p.status] ?? "neutral"}>
              {STATUS_LABEL[p.status] ?? p.status}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-text-muted">{data}</p>
        </div>
        {p.foto_url ? (
          // Supabase Storage não está em remotePatterns do next.config; usamos <img> aqui.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={p.foto_url}
            alt=""
            className="h-16 w-16 rounded-md object-cover"
            loading="lazy"
          />
        ) : null}
      </Card>
    </Link>
  );
}
