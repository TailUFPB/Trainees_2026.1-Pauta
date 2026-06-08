import { VenetianMask } from "lucide-react";

// Badge para publicações anônimas. Ícone + texto (não cor sozinha) para
// acessibilidade: usuários com daltonismo precisam de mais de um sinal.
export function AnonimoBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-pill border border-border bg-surface px-2 py-0.5 text-xs font-medium text-text-muted"
      aria-label="Publicação anônima"
    >
      <VenetianMask aria-hidden className="h-3 w-3" />
      Anônimo
    </span>
  );
}
