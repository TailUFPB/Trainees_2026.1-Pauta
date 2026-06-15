import { cn } from "@/lib/design/cn";

interface LogoMarkProps {
  className?: string;
  title?: string;
}

/**
 * Marca da Pauta: uma bandeira fincada no mapa.
 * Significa, ao mesmo tempo, "levantar uma pauta" e "marcar um ponto no mapa"
 * — as duas ações centrais da plataforma.
 *
 * A haste usa a cor do texto (var(--color-text)) e a bandeira usa o destaque
 * (var(--color-accent)), então o ícone se adapta sozinho a tema claro/escuro.
 */
export function LogoMark({ className, title }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role={title ? "img" : "presentation"}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      className={cn("h-6 w-6", className)}
    >
      {title ? <title>{title}</title> : null}
      {/* bandeira */}
      <path
        d="M5.5 3.4h10.7L13 7.05l3.2 3.65H5.5z"
        fill="var(--color-accent)"
      />
      {/* haste */}
      <path
        d="M5.5 2.6v18.8"
        stroke="var(--color-text)"
        strokeWidth="2.1"
        strokeLinecap="round"
      />
      {/* base fincada no mapa */}
      <circle cx="5.5" cy="21" r="1.9" fill="var(--color-text)" />
    </svg>
  );
}

interface LogoProps {
  className?: string;
  /** Esconde o nome e mostra só a marca (ex.: favicons, telas estreitas). */
  markOnly?: boolean;
}

/** Marca + nome "Pauta". Use no header, footer e telas de marca. */
export function Logo({ className, markOnly = false }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark className="h-6 w-6" title={markOnly ? "Pauta" : undefined} />
      {markOnly ? null : (
        <span className="font-display text-xl font-bold tracking-tight text-text">
          Pauta
        </span>
      )}
    </span>
  );
}
