"use client";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/design/cn";

const button = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-sans font-medium transition-[transform,background-color,border-color,color,box-shadow] duration-150 ease-[cubic-bezier(0.16,1,0.3,1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98] select-none",
  {
    variants: {
      variant: {
        primary:
          "bg-accent text-white shadow-[0_1px_2px_rgba(15,23,42,0.04),0_1px_3px_rgba(15,23,42,0.06)] hover:bg-accent-hover hover:shadow-[0_10px_30px_rgba(255,107,53,0.25),0_4px_12px_rgba(255,107,53,0.15)]",
        secondary:
          "border border-border-strong bg-surface text-text hover:border-text hover:bg-bg",
        ghost: "text-text hover:bg-surface",
        invert: "bg-bg text-text hover:bg-white",
      },
      size: {
        sm: "h-9 px-3 text-sm rounded-md min-w-[44px]",
        md: "h-11 px-5 text-base rounded-md",
        lg: "h-14 px-7 text-lg rounded-lg",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild, loading, disabled, children, ...rest },
  ref,
) {
  const Comp = asChild ? Slot : "button";
  const content = asChild ? (
    children
  ) : (
    <>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
      {children}
    </>
  );
  return (
    <Comp
      ref={ref}
      className={cn(button({ variant, size }), className)}
      disabled={disabled || loading}
      {...rest}
    >
      {content}
    </Comp>
  );
});
