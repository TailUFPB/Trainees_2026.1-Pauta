import { cn } from "@/lib/design/cn";
import type { HTMLAttributes } from "react";

type Tone = "default" | "muted" | "inverted";

const TONES: Record<Tone, string> = {
  default: "bg-bg text-text",
  muted: "bg-surface text-text",
  inverted: "bg-surface-inverted text-bg",
};

interface Props extends HTMLAttributes<HTMLElement> {
  tone?: Tone;
  spacing?: "default" | "tight" | "loose";
}

const SPACING = {
  tight: "py-12 md:py-16",
  default: "py-16 md:py-24",
  loose: "py-20 md:py-32",
} as const;

export function Section({
  tone = "default",
  spacing = "default",
  className,
  children,
  ...rest
}: Props) {
  return (
    <section
      className={cn("relative", TONES[tone], SPACING[spacing], className)}
      {...rest}
    >
      {children}
    </section>
  );
}
