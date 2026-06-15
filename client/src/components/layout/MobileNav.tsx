"use client";
import * as Dialog from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/primitives/Button";
import { NAV_PUBLICO } from "@/lib/nav";

interface Props {
  onSignIn: () => void;
}

export function MobileNav({ onSignIn }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          className="ml-auto inline-grid h-11 w-11 place-items-center rounded-md text-text md:hidden"
          aria-label="Abrir menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-[#0a0e1a]/60 backdrop-blur-sm md:hidden" />
        <Dialog.Content className="fixed right-0 top-0 z-50 h-full w-[min(320px,90vw)] bg-bg p-6 shadow-[var(--shadow-2)] md:hidden">
          <Dialog.Title className="sr-only">Menu</Dialog.Title>
          <div className="flex items-center justify-between">
            <span className="font-display text-lg font-bold text-text">Menu</span>
            <Dialog.Close
              aria-label="Fechar"
              className="grid h-11 w-11 place-items-center rounded-md text-text-muted hover:text-text"
            >
              <X className="h-5 w-5" />
            </Dialog.Close>
          </div>
          <nav className="mt-8 flex flex-col gap-1" aria-label="Navegação mobile">
            {NAV_PUBLICO.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-md px-3 py-3 text-base font-medium text-text hover:bg-surface"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-8 border-t border-border pt-6">
            <Button
              variant="primary"
              onClick={() => {
                setOpen(false);
                onSignIn();
              }}
              className="w-full"
            >
              Entrar
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
