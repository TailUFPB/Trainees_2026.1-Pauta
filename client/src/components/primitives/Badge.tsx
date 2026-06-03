import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/design/cn";

const badge = cva(
  "inline-flex items-center gap-1.5 rounded-pill px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "bg-surface text-text-muted border border-border",
        success: "bg-success/10 text-success border border-success/30",
        accent: "bg-accent/10 text-accent border border-accent/30",
        danger: "bg-danger/10 text-danger border border-danger/30",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

interface Props
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badge> {}

export function Badge({ tone, className, children, ...rest }: Props) {
  return (
    <span className={cn(badge({ tone }), className)} {...rest}>
      {children}
    </span>
  );
}
