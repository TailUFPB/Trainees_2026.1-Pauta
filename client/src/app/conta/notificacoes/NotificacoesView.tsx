"use client";

import { Bell, Check, ExternalLink, Loader2, Mail, Smartphone } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Button } from "@/components/primitives/Button";
import { api } from "@/lib/api/client";
import type { Notificacao, PreferenciasNotificacao } from "@/lib/api/types";

interface Props {
  initial: Notificacao[];
  initialPrefs: PreferenciasNotificacao;
}

const PREFERENCE_OPTIONS: Array<{
  key: keyof Pick<
    PreferenciasNotificacao,
    "interna" | "email" | "push" | "problemas_perto" | "politicos"
  >;
  label: string;
  description: string;
}> = [
  {
    key: "interna",
    label: "Central interna",
    description: "Guardar alertas na sua conta do Pauta.",
  },
  {
    key: "email",
    label: "Email",
    description: "Receber mensagens quando o envio por email estiver configurado.",
  },
  {
    key: "push",
    label: "Push",
    description: "Receber alertas no navegador quando o dispositivo estiver conectado.",
  },
  {
    key: "problemas_perto",
    label: "Problemas perto de mim",
    description: "Avisar sobre novos problemas dentro da sua regiao.",
  },
  {
    key: "politicos",
    label: "Politicos acompanhados",
    description: "Avisar quando houver novidades sobre politicos que voce segue.",
  },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function NotificacoesView({ initial, initialPrefs }: Props) {
  const [items, setItems] = useState(initial);
  const [prefs, setPrefs] = useState(initialPrefs);
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [savingPreference, setSavingPreference] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
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

  const togglePreference = async (
    key: keyof Pick<
      PreferenciasNotificacao,
      "interna" | "email" | "push" | "problemas_perto" | "politicos"
    >,
  ) => {
    const next = !prefs[key];
    setSavingPreference(key);
    setError(null);
    try {
      const result = await api.atualizarPreferenciasNotificacao({ [key]: next });
      setPrefs(result.prefs_notificacao);
    } catch {
      setError("Não foi possível salvar a preferência.");
    } finally {
      setSavingPreference(null);
    }
  };

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-10 px-4 pb-16 lg:grid-cols-[minmax(0,1fr)_320px]">
      <section aria-labelledby="lista-notificacoes">
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

        {notice ? (
          <p className="mb-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            {notice}
          </p>
        ) : null}

        {items.length === 0 ? (
          <div className="border-y border-border py-14 text-center">
            <Bell className="mx-auto h-7 w-7 text-text-muted" aria-hidden />
            <h3 className="mt-4 font-display text-lg font-semibold text-text">
              Sua central esta vazia
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

      <aside aria-labelledby="preferencias-notificacoes" className="lg:border-l lg:border-border lg:pl-8">
        <h2 id="preferencias-notificacoes" className="font-display text-xl font-semibold text-text">
          Preferências
        </h2>
        <p className="mt-1 text-sm leading-6 text-text-muted">
          Escolha quais alertas podem ser entregues em cada canal.
        </p>
        <div className="mt-5 divide-y divide-border border-y border-border">
          {PREFERENCE_OPTIONS.map((option) => (
            <label key={option.key} className="flex cursor-pointer gap-3 py-4">
              <input
                type="checkbox"
                checked={prefs[option.key]}
                disabled={savingPreference === option.key}
                onChange={() => void togglePreference(option.key)}
                className="mt-0.5 h-4 w-4 accent-[var(--color-accent)]"
              />
              <span className="min-w-0">
                <span className="flex items-center gap-2 text-sm font-medium text-text">
                  {option.key === "email" ? <Mail className="h-4 w-4" aria-hidden /> : null}
                  {option.key === "push" ? <Smartphone className="h-4 w-4" aria-hidden /> : null}
                  {option.label}
                </span>
                <span className="mt-1 block text-xs leading-5 text-text-muted">
                  {option.description}
                </span>
              </span>
            </label>
          ))}
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="mt-5 w-full"
          loading={testing}
          onClick={async () => {
            setError(null);
            setNotice(null);
            setTesting(true);
            try {
              const response = await fetch("/api/notificacoes/teste", { method: "POST" });
              if (!response.ok) throw new Error("teste rejeitado");
              setNotice("Evento de teste registrado. O worker criará a notificação em alguns segundos.");

              window.setTimeout(async () => {
                try {
                  const updated = await api.notificacoes({ limite: 50, offset: 0 });
                  setItems(updated);
                  window.dispatchEvent(new Event("pauta:notificacoes-atualizadas"));
                } catch {
                  // O evento continua salvo no outbox e pode ser processado depois.
                }
              }, 12_000);
            } catch {
              setError("Não foi possível solicitar uma notificação de teste.");
            } finally {
              setTesting(false);
            }
          }}
        >
          Enviar notificação de teste
        </Button>
      </aside>
    </div>
  );
}
