import { cn } from "@/lib/design/cn";
import type { HTMLAttributes } from "react";

interface Props extends HTMLAttributes<HTMLDivElement> {
  tone?: "accent" | "muted";
}

export function Eyebrow({
  tone = "accent",
  className,
  children,
  ...rest
}: Props) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.18em]",
        tone === "accent" ? "text-accent" : "text-text-muted",
        className,
      )}
      {...rest}
    >
      <span aria-hidden className="inline-block h-px w-6 bg-current opacity-60" />
      {children}
    </div>
  );
}
