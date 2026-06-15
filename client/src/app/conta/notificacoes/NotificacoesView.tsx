"use client";

import { Bell, Check, ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { api } from "@/lib/api/client";
import type { Notificacao } from "@/lib/api/types";

interface Props {
  initial: Notificacao[];
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

// Central de notificações — caixa de entrada pura. As preferências de canal e a
// localização vivem em /conta/configuracoes.
export function NotificacoesView({ initial }: Props) {
  const [items, setItems] = useState(initial);
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const unread = useMemo(() => items.filter((item) => !item.lida).length, [items]);

  const markRead = async (id: string) => {
    setMarkingId(id);
    setError(null);
    try {
      const updated = await api.marcarNotificacaoLida(id);
      setItems((current) => current.map((item) => (item.id === id ? updated : item)));
      window.dispatchEvent(new Event("pauta:notificacoes-atualizadas"));
    } catch {
      setError("Não foi possível marcar a notificação como lida.");
    } finally {
      setMarkingId(null);
    }
  };

  return (
    <section
      aria-labelledby="lista-notificacoes"
      className="mx-auto w-full max-w-2xl px-4 pb-16"
    >
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 id="lista-notificacoes" className="font-display text-xl font-semibold text-text">
            Histórico
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            {unread === 0 ? "Nenhuma notificação nova" : `${unread} não lida${unread > 1 ? "s" : ""}`}
          </p>
        </div>
      </div>

      {error ? (
        <p className="mb-4 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </p>
      ) : null}

      {items.length === 0 ? (
        <div className="border-y border-border py-14 text-center">
          <Bell className="mx-auto h-7 w-7 text-text-muted" aria-hidden />
          <h3 className="mt-4 font-display text-lg font-semibold text-text">
            Sua central está vazia
          </h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-text-muted">
            Novidades sobre problemas e políticos acompanhados aparecerão aqui.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {items.map((item) => (
            <li
              key={item.id}
              className={`grid gap-3 py-5 sm:grid-cols-[12px_minmax(0,1fr)_auto] ${
                item.lida ? "opacity-70" : ""
              }`}
            >
              <span
                className={`mt-2 h-2.5 w-2.5 rounded-full ${item.lida ? "bg-border-strong" : "bg-accent"}`}
                aria-hidden
              />
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <h3 className="font-semibold text-text">{item.titulo}</h3>
                  <time className="text-xs text-text-muted" dateTime={item.created_at}>
                    {formatDate(item.created_at)}
                  </time>
                </div>
                <p className="mt-1 text-sm leading-6 text-text-muted">{item.mensagem}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {item.link_destino ? (
                    <Link
                      href={item.link_destino}
                      className="inline-flex items-center gap-1 text-sm font-medium text-info hover:underline"
                    >
                      Ver detalhes <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                    </Link>
                  ) : null}
                  {!item.lida ? (
                    <button
                      type="button"
                      onClick={() => void markRead(item.id)}
                      disabled={markingId === item.id}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm font-medium text-text-muted hover:bg-surface hover:text-text disabled:opacity-50"
                    >
                      {markingId === item.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                      ) : (
                        <Check className="h-3.5 w-3.5" aria-hidden />
                      )}
                      Marcar como lida
                    </button>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
