"use client";
import { cn } from "@/lib/design/cn";

const CITIES = [
  { name: "João Pessoa", x: 290, y: 128, delay: 0 },
  { name: "Bayeux", x: 281, y: 127, delay: 0.6 },
  { name: "Santa Rita", x: 273, y: 130, delay: 1.2 },
  { name: "Campina Grande", x: 208, y: 140, delay: 1.8 },
] as const;

// 14 dots "problemas reportados" hand-posicionados dentro do contorno.
const PROBLEM_DOTS = [
  { x: 60, y: 110, status: "ativo" },
  { x: 72, y: 130, status: "resolvido" },
  { x: 96, y: 118, status: "ativo" },
  { x: 100, y: 148, status: "resolvido" },
  { x: 124, y: 142, status: "ativo" },
  { x: 148, y: 128, status: "ativo" },
  { x: 168, y: 150, status: "ativo" },
  { x: 170, y: 118, status: "resolvido" },
  { x: 188, y: 140, status: "ativo" },
  { x: 204, y: 124, status: "ativo" },
  { x: 220, y: 110, status: "ativo" },
  { x: 222, y: 144, status: "ativo" },
  { x: 240, y: 124, status: "resolvido" },
  { x: 258, y: 140, status: "ativo" },
] as const;

const PB_PATH =
  "M22,118 L38,96 L62,82 L88,76 L114,82 L134,72 L156,78 L178,72 L196,82 L218,76 L238,86 L256,82 L278,98 L296,112 L304,128 L296,142 L282,148 L266,154 L246,150 L228,158 L206,160 L184,156 L162,162 L140,158 L118,164 L94,160 L72,156 L52,148 L36,138 Z";

interface Props {
  className?: string;
}

export function StylizedMap({ className }: Props) {
  return (
    <div
      className={cn(
        "relative aspect-[320/240] w-full max-w-xl",
        className,
      )}
      role="img"
      aria-label="Mapa estilizado da Paraíba preenchido com pontos representando problemas reportados — laranja para abertos, verde para resolvidos. Pontos pulsam em João Pessoa, Bayeux, Santa Rita e Campina Grande."
    >
      <svg
        viewBox="0 0 320 240"
        className="absolute inset-0 h-full w-full"
        aria-hidden
      >
        <defs>
          <pattern
            id="pauta-dotted-territory"
            x="0"
            y="0"
            width="9"
            height="9"
            patternUnits="userSpaceOnUse"
          >
            <circle
              cx="4.5"
              cy="4.5"
              r="0.9"
              fill="var(--color-border-strong)"
              fillOpacity="0.55"
            />
          </pattern>
          <clipPath id="pauta-pb-clip">
            <path d={PB_PATH} />
          </clipPath>
          <radialGradient id="pauta-glow" cx="55%" cy="55%" r="55%">
            <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.16" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
          </radialGradient>
        </defs>

        <rect width="320" height="220" fill="url(#pauta-glow)" />

        <path
          d={PB_PATH}
          fill="url(#pauta-dotted-territory)"
          stroke="var(--color-text)"
          strokeWidth="1.25"
          strokeLinejoin="round"
          strokeOpacity="0.45"
        />

        <g clipPath="url(#pauta-pb-clip)">
          {PROBLEM_DOTS.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="2.2"
              fill={
                p.status === "resolvido"
                  ? "var(--color-success)"
                  : "var(--color-accent)"
              }
              fillOpacity={p.status === "resolvido" ? 0.75 : 0.95}
            />
          ))}
        </g>

        <g
          stroke="var(--color-accent)"
          strokeOpacity="0.22"
          strokeWidth="0.8"
          strokeDasharray="2 4"
          fill="none"
        >
          <path d="M208,140 L273,130" />
          <path d="M273,130 L281,127" />
          <path d="M281,127 L290,128" />
        </g>

        {CITIES.map((c) => (
          <g key={c.name} transform={`translate(${c.x},${c.y})`}>
            <circle
              r="6"
              className="pauta-pulse-ring"
              fill="var(--color-accent)"
              fillOpacity="0.35"
              style={{ animationDelay: `${c.delay}s` }}
            />
            <circle
              r="4"
              fill="var(--color-accent)"
              stroke="var(--color-bg)"
              strokeWidth="1.5"
            />
          </g>
        ))}
      </svg>

      <div className="pointer-events-none absolute inset-0 hidden md:block">
        {CITIES.map((c) => (
          <span
            key={c.name}
            className="absolute -translate-x-1/2 translate-y-3 whitespace-nowrap font-mono text-[10px] uppercase tracking-wider text-text-muted"
            style={{
              left: `${(c.x / 320) * 100}%`,
              top: `${(c.y / 240) * 100}%`,
            }}
          >
            {c.name}
          </span>
        ))}
      </div>

      <div className="absolute bottom-0 left-0 right-0 flex items-center justify-center gap-4 pb-0.5 font-mono text-[10px] uppercase tracking-wider text-text-muted">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-pill bg-accent" /> Aberto
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-pill bg-success" /> Resolvido
        </span>
      </div>
    </div>
  );
}
