import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/primitives/Badge";
import { Card } from "@/components/primitives/Card";
import type { Politico } from "@/lib/api/types";
import { politicoFotoSrc } from "@/lib/politico-foto";
import { SeguirButton } from "./SeguirButton";

interface Props {
  politico: Politico;
}

// O card não é mais um único link gigante: o corpo informa, o perfil externo
// é um link discreto e "Seguir" é uma ação distinta — evitando interativos
// aninhados e expondo o follow que antes não tinha entrada na UI.
export function CandidatoCard({ politico: p }: Props) {
  return (
    <Card className="flex h-full flex-col gap-4">
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
          {p.partido ? (
            <div className="mt-2">
              <Badge>{p.partido}</Badge>
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-auto flex items-center justify-between gap-3">
        <SeguirButton politicoId={p.id} />
        {p.url_perfil ? (
          <Link
            href={p.url_perfil}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-1 rounded-md text-sm font-medium text-text-muted outline-none transition-colors hover:text-text focus-visible:ring-2 focus-visible:ring-accent"
          >
            Ver perfil
            <ArrowUpRight className="h-4 w-4" aria-hidden />
          </Link>
        ) : null}
      </div>
    </Card>
  );
}
