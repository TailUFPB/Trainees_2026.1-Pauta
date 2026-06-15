"use client";

import { Mail, MapPin, Smartphone } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/primitives/Badge";
import { Button } from "@/components/primitives/Button";
import { api } from "@/lib/api/client";
import type { PreferenciasNotificacao } from "@/lib/api/types";
import { ativarPush } from "@/lib/firebase/push";

interface Props {
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
    description: "Avisar sobre novos problemas dentro da sua região.",
  },
  {
    key: "politicos",
    label: "Políticos acompanhados",
    description: "Avisar quando houver novidades sobre políticos que você segue.",
  },
];

// Mensagens de falha ao ativar push, por motivo retornado por ativarPush().
const PUSH_ERROR_MESSAGES: Record<string, string> = {
  "sem-config": "Notificações push ainda não estão configuradas neste ambiente.",
  "nao-suportado": "Este navegador não suporta notificações push.",
  "permissao-negada": "Permissão de notificações negada pelo navegador.",
  erro: "Não foi possível ativar as notificações push.",
};

export function ConfiguracoesView({ initialPrefs }: Props) {
  const [prefs, setPrefs] = useState(initialPrefs);
  const [savingPreference, setSavingPreference] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [coord, setCoord] = useState<{ lat: number; lng: number } | null>(null);
  const [savingLocal, setSavingLocal] = useState(false);
  const [localNotice, setLocalNotice] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const togglePreference = async (
    key: keyof Pick<
      PreferenciasNotificacao,
      "interna" | "email" | "push" | "problemas_perto" | "politicos"
    >,
  ) => {
    const next = !prefs[key];
    setSavingPreference(key);
    setError(null);
    setNotice(null);
    try {
      // Ao LIGAR push: pede permissão, registra SW e salva o token antes de
      // persistir a preferência. Se falhar, não liga o toggle.
      if (key === "push" && next) {
        const resultado = await ativarPush();
        if (!resultado.ok) {
          setError(PUSH_ERROR_MESSAGES[resultado.motivo] ?? PUSH_ERROR_MESSAGES.erro);
          return;
        }
      }
      const result = await api.atualizarPreferenciasNotificacao({ [key]: next });
      setPrefs(result.prefs_notificacao);
      if (key === "push" && next) {
        setNotice("Notificações push ativadas neste dispositivo.");
      }
    } catch {
      setError("Não foi possível salvar a preferência.");
    } finally {
      setSavingPreference(null);
    }
  };

  const capturarLocalizacao = () => {
    if (!("geolocation" in navigator)) {
      setLocalError("Geolocalização não disponível neste dispositivo.");
      return;
    }
    setLocalError(null);
    setLocalNotice(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setCoord({ lat, lng });
        setSavingLocal(true);
        try {
          await api.definirLocalizacao(lat, lng);
          setLocalNotice("Localização salva. Você receberá alertas de problemas próximos.");
        } catch {
          setLocalError("Não foi possível salvar sua localização.");
        } finally {
          setSavingLocal(false);
        }
      },
      () => setLocalError("Não foi possível obter sua localização."),
    );
  };

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-12 px-4 pb-16">
      <section aria-labelledby="preferencias-notificacoes">
        <h2
          id="preferencias-notificacoes"
          className="font-display text-xl font-semibold text-text"
        >
          Preferências de notificação
        </h2>
        <p className="mt-1 text-sm leading-6 text-text-muted">
          Escolha quais alertas podem ser entregues em cada canal.
        </p>

        {error ? (
          <p className="mt-4 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        ) : null}
        {notice ? (
          <p className="mt-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            {notice}
          </p>
        ) : null}

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
          className="mt-5"
          loading={testing}
          onClick={async () => {
            setError(null);
            setNotice(null);
            setTesting(true);
            try {
              const response = await fetch("/api/notificacoes/teste", { method: "POST" });
              if (!response.ok) throw new Error("teste rejeitado");
              setNotice(
                "Evento de teste registrado. A notificação aparecerá na sua central em alguns segundos.",
              );
              window.setTimeout(() => {
                window.dispatchEvent(new Event("pauta:notificacoes-atualizadas"));
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
      </section>

      <section aria-labelledby="minha-localizacao">
        <h2 id="minha-localizacao" className="font-display text-xl font-semibold text-text">
          Minha localização
        </h2>
        <p className="mt-1 text-sm leading-6 text-text-muted">
          Define sua região base. Necessária para alertas de “Problemas perto de mim”.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={capturarLocalizacao}
            loading={savingLocal}
          >
            <MapPin className="h-4 w-4" aria-hidden />
            {coord ? "Atualizar localização" : "Usar minha localização"}
          </Button>
          {coord ? (
            <Badge tone="success">
              {coord.lat.toFixed(4)}, {coord.lng.toFixed(4)}
            </Badge>
          ) : null}
        </div>

        {localError ? (
          <p className="mt-4 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {localError}
          </p>
        ) : null}
        {localNotice ? (
          <p className="mt-4 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            {localNotice}
          </p>
        ) : null}
      </section>
    </div>
  );
}
