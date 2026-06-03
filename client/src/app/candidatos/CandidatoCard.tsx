import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/primitives/Badge";
import { Card } from "@/components/primitives/Card";
import type { Politico } from "@/lib/api/types";
import { politicoFotoSrc } from "@/lib/politico-foto";

interface Props {
  politico: Politico;
}

export function CandidatoCard({ politico: p }: Props) {
  const inner = (
    <Card interactive className="flex h-full flex-col gap-4">
      <div className="flex items-start gap-4">
        <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-pill border border-border">
          <Image
            src={politicoFotoSrc(p)}
            alt={p.nome}
            fill
            sizes="64px"
            className="object-cover"
          />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-display text-lg font-bold tracking-tight text-text">
            {p.nome}
          </h3>
          <p className="truncate text-sm text-text-muted">
            {p.cargo ?? "Vereador(a)"} · {p.municipio ?? "PB"}
          </p>
        </div>
        {p.url_perfil ? (
          <ArrowUpRight className="h-4 w-4 text-text-muted" aria-hidden />
        ) : null}
      </div>
      {p.partido ? <Badge>{p.partido}</Badge> : null}
    </Card>
  );

  if (p.url_perfil) {
    return (
      <Link
        href={p.url_perfil}
        target="_blank"
        rel="noreferrer noopener"
        className="block"
      >
        {inner}
      </Link>
    );
  }
  return inner;
}
