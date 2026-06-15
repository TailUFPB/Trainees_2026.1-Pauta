"use client";
import { useContext } from "react";
import {
  SessionContext,
  type SessionUser,
} from "@/components/auth/SessionProvider";

export type { SessionUser };

export function useSession(): { user: SessionUser | null; loading: boolean } {
  const { user, loading } = useContext(SessionContext);
  return { user, loading };
}
