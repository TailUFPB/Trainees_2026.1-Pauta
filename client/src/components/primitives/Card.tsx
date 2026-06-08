import { cn } from "@/lib/design/cn";
import type { HTMLAttributes } from "react";

interface Props extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export function Card({ interactive, className, children, ...rest }: Props) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-surface p-6 shadow-[var(--shadow-1)]",
        interactive &&
          "transition-[transform,box-shadow,border-color] duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[var(--shadow-3)]",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
