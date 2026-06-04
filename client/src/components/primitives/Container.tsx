import { cn } from "@/lib/design/cn";
import type { HTMLAttributes } from "react";

type Size = "narrow" | "default" | "wide";

const SIZES: Record<Size, string> = {
  narrow: "max-w-3xl",
  default: "max-w-6xl",
  wide: "max-w-7xl",
};

interface Props extends HTMLAttributes<HTMLDivElement> {
  size?: Size;
}

export function Container({ size = "default", className, children, ...rest }: Props) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-6 md:px-8",
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
