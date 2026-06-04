import { cn } from "@/lib/design/cn";
import type { HTMLAttributes } from "react";

export function Skeleton({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-border/60",
        className,
      )}
      aria-hidden
      {...rest}
    />
  );
}
