import Link from "next/link";
import { Badge } from "@/components/primitives/Badge";
import { Card } from "@/components/primitives/Card";
import type { Problema } from "@/lib/api/types";
import { statusLabel, statusTone } from "@/lib/problema-status";

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
            <Badge tone={statusTone(p.status)}>{statusLabel(p.status)}</Badge>
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
