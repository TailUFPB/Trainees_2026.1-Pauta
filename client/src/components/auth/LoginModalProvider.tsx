"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { LoginModal } from "./LoginModal";

const STORAGE_KEY = "pauta-auth-redirect";

interface Ctx {
  open: (redirectTo?: string) => void;
  close: () => void;
  isOpen: boolean;
}

const LoginModalContext = createContext<Ctx | null>(null);

export function useLoginModal() {
  const ctx = useContext(LoginModalContext);
  if (!ctx) throw new Error("useLoginModal precisa de <LoginModalProvider>");
  return ctx;
}

export function consumeRedirect(): string | null {
  if (typeof window === "undefined") return null;
  const r = sessionStorage.getItem(STORAGE_KEY);
  sessionStorage.removeItem(STORAGE_KEY);
  return r;
}

export function LoginModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const searchParams = useSearchParams();

  const open = useCallback((redirectTo?: string) => {
    if (redirectTo && typeof window !== "undefined") {
      sessionStorage.setItem(STORAGE_KEY, redirectTo);
    }
    setIsOpen(true);
  }, []);

  useEffect(() => {
    if (searchParams.get("login") === "1") {
      const redirectTo = searchParams.get("redirectTo") ?? undefined;
      open(redirectTo);
    }
  }, [searchParams, open]);

  const close = useCallback(() => setIsOpen(false), []);

  const value = useMemo(() => ({ open, close, isOpen }), [open, close, isOpen]);

  return (
    <LoginModalContext.Provider value={value}>
      {children}
      <LoginModal open={isOpen} onOpenChange={setIsOpen} />
    </LoginModalContext.Provider>
  );
}
