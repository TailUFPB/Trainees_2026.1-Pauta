"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

const REFRESH_MS = 30_000;

export function NotificationBell() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let active = true;

    const refresh = async () => {
      try {
        const result = await api.contagemNotificacoes();
        if (active) setCount(result.nao_lidas);
      } catch {
        if (active) setCount(0);
      }
    };

    void refresh();
    const interval = window.setInterval(refresh, REFRESH_MS);
    window.addEventListener("pauta:notificacoes-atualizadas", refresh);
    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("pauta:notificacoes-atualizadas", refresh);
    };
  }, []);

  const label = count > 0 ? `${count} notificações não lidas` : "Notificações";

  return (
    <Link
      href="/conta/notificacoes"
      aria-label={label}
      title={label}
      className="relative inline-grid h-9 w-9 shrink-0 place-items-center rounded-md text-text-muted transition-colors hover:bg-surface hover:text-text"
    >
      <Bell className="h-5 w-5" aria-hidden />
      {count > 0 ? (
        <span className="absolute right-0 top-0 grid min-h-4 min-w-4 place-items-center rounded-full bg-danger px-1 text-[10px] font-bold leading-4 text-white">
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
    </Link>
  );
}
