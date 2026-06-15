"use client";
import { createContext, type ReactNode } from "react";

export type SessionUser = { id: string; email: string | null };

export type SessionContextValue = {
  user: SessionUser | null;
  loading: boolean;
};

export const SessionContext = createContext<SessionContextValue>({
  user: null,
  loading: false,
});

export function SessionProvider({
  initialUser,
  children,
}: {
  initialUser: SessionUser | null;
  children: ReactNode;
}) {
  // O servidor já resolveu a autenticação antes do render, então não há
  // fase de loading assíncrona no browser — `loading` é sempre `false`.
  return (
    <SessionContext.Provider value={{ user: initialUser, loading: false }}>
      {children}
    </SessionContext.Provider>
  );
}
