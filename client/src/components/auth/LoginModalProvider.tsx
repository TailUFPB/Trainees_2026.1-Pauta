"use client";
import {
  createContext,
  Suspense,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
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

/**
 * Lê ?login=1[&redirectTo=...] da URL e abre o modal automaticamente.
 *
 * Isolado em componente próprio porque useSearchParams() força o Next a fazer
 * client-side bailout — wrap em <Suspense> evita quebrar o prerender estático
 * de páginas que herdam o RootLayout (notavelmente /_not-found).
 */
function QueryParamLoginOpener() {
  const searchParams = useSearchParams();
  const { open } = useLoginModal();

  useEffect(() => {
    if (searchParams.get("login") === "1") {
      const redirectTo = searchParams.get("redirectTo") ?? undefined;
      // eslint-disable-next-line react-hooks/set-state-in-effect
      open(redirectTo);
    }
  }, [searchParams, open]);

  return null;
}

export function LoginModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback((redirectTo?: string) => {
    if (redirectTo && typeof window !== "undefined") {
      sessionStorage.setItem(STORAGE_KEY, redirectTo);
    }
    setIsOpen(true);
  }, []);

  const close = useCallback(() => setIsOpen(false), []);

  const value = useMemo(() => ({ open, close, isOpen }), [open, close, isOpen]);

  return (
    <LoginModalContext.Provider value={value}>
      <Suspense fallback={null}>
        <QueryParamLoginOpener />
      </Suspense>
      {children}
      <LoginModal open={isOpen} onOpenChange={setIsOpen} />
    </LoginModalContext.Provider>
  );
}
