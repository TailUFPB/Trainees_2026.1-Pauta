import { cn } from "@/lib/design/cn";
import type { ElementType, HTMLAttributes } from "react";

type Level = 1 | 2 | 3 | 4;
type Size = "hero" | "display" | "h1" | "h2" | "h3" | "h4";

const SIZES: Record<Size, string> = {
  hero: "font-display font-bold tracking-[-0.03em] leading-[1.02] text-[length:var(--text-hero,clamp(3.5rem,2.5rem+5vw,6rem))]",
  display: "font-display font-bold tracking-[-0.025em] leading-[1.05] text-[length:clamp(3rem,2.25rem+3.75vw,4.5rem)]",
  h1: "font-display font-bold tracking-[-0.02em] leading-[1.1] text-[length:clamp(2.375rem,1.75rem+3.125vw,3.5rem)]",
  h2: "font-display font-bold tracking-[-0.015em] leading-[1.15] text-[length:clamp(1.875rem,1.5rem+1.875vw,2.5rem)]",
  h3: "font-sans font-semibold tracking-[-0.01em] leading-[1.25] text-[length:clamp(1.5rem,1.35rem+0.75vw,1.75rem)]",
  h4: "font-sans font-semibold tracking-tight leading-snug text-[length:clamp(1.25rem,1.15rem+0.45vw,1.375rem)]",
};

interface Props extends HTMLAttributes<HTMLHeadingElement> {
  as?: ElementType;
  level?: Level;
  size?: Size;
}

export function Heading({
  as,
  level = 2,
  size = "h2",
  className,
  children,
  ...rest
}: Props) {
  const Tag = (as ?? (`h${level}` as ElementType));
  return (
    <Tag className={cn(SIZES[size], "text-text", className)} {...rest}>
      {children}
    </Tag>
  );
}
