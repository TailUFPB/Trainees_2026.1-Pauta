"use client";
import * as Dialog from "@radix-ui/react-dialog";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/design/cn";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  hideTitle?: boolean;
  children: ReactNode;
  className?: string;
}

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  hideTitle,
  children,
  className,
}: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay
          className={cn(
            "fixed inset-0 z-40 bg-[#0a0e1a]/60 backdrop-blur-sm",
            "data-[state=open]:animate-[fadeIn_200ms_cubic-bezier(0.16,1,0.3,1)]",
          )}
        />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-[min(440px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface p-7 text-text shadow-[var(--shadow-2)]",
            "data-[state=open]:animate-[modalIn_250ms_cubic-bezier(0.16,1,0.3,1)]",
            "max-md:bottom-0 max-md:top-auto max-md:left-0 max-md:right-0 max-md:w-full max-md:translate-x-0 max-md:translate-y-0 max-md:rounded-b-none max-md:rounded-t-lg",
            className,
          )}
        >
          {hideTitle ? (
            <VisuallyHidden asChild>
              <Dialog.Title>{title}</Dialog.Title>
            </VisuallyHidden>
          ) : (
            <Dialog.Title className="font-display text-2xl font-bold tracking-tight text-text">
              {title}
            </Dialog.Title>
          )}
          {description ? (
            <Dialog.Description className="mt-2 text-sm text-text-muted">
              {description}
            </Dialog.Description>
          ) : null}
          <Dialog.Close
            aria-label="Fechar"
            className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-md text-text-muted transition-colors hover:bg-bg hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <X className="h-4 w-4" />
          </Dialog.Close>
          <div className="mt-6">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
