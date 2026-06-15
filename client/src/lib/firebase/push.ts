"use client";
import { getMessaging, getToken, isSupported, onMessage } from "firebase/messaging";
import { api } from "@/lib/api/client";
import {
  firebaseConfigCompleto,
  firebaseConfigQuery,
  getFirebaseApp,
  vapidKey,
} from "./config";

export type PushResultado =
  | { ok: true; token: string }
  | {
      ok: false;
      motivo: "sem-config" | "nao-suportado" | "permissao-negada" | "erro";
      detalhe?: string;
    };

/** Mesmo mapeamento do service worker (manter em sincronia). */
function telaParaUrl(dados: Record<string, unknown> | undefined): string {
  switch (dados?.tela) {
    case "mapa":
      return "/mapa";
    case "problema_detalhe":
      return dados?.problema_id ? `/conta/reportes/${dados.problema_id}` : "/mapa";
    case "perfil_politico":
      return "/candidatos";
    default:
      return "/conta/notificacoes";
  }
}

/** Verifica suporte do navegador (Notification + Service Worker + FCM). */
export async function suportaPush(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  if (!("Notification" in window) || !("serviceWorker" in navigator)) return false;
  try {
    return await isSupported();
  } catch {
    return false;
  }
}

/**
 * Fluxo completo: pede permissão, registra o service worker, gera o token FCM
 * e salva no backend (PATCH /usuarios/me/notificacoes com merge de token_fcm).
 */
export async function ativarPush(): Promise<PushResultado> {
  if (!firebaseConfigCompleto()) return { ok: false, motivo: "sem-config" };
  if (!(await suportaPush())) return { ok: false, motivo: "nao-suportado" };

  try {
    const permissao = await Notification.requestPermission();
    if (permissao !== "granted") return { ok: false, motivo: "permissao-negada" };

    const registration = await navigator.serviceWorker.register(
      `/firebase-messaging-sw.js?${firebaseConfigQuery()}`,
    );
    await navigator.serviceWorker.ready;

    const messaging = getMessaging(getFirebaseApp());
    const token = await getToken(messaging, {
      vapidKey,
      serviceWorkerRegistration: registration,
    });
    if (!token) return { ok: false, motivo: "erro", detalhe: "token vazio" };

    await api.atualizarPreferenciasNotificacao({ token_fcm: token });
    return { ok: true, token };
  } catch (e) {
    return { ok: false, motivo: "erro", detalhe: e instanceof Error ? e.message : String(e) };
  }
}

/**
 * Listener de mensagens com o app em foreground: mostra notificação do SO,
 * atualiza o contador do sino e habilita roteamento no clique.
 * Retorna função de cleanup (ou no-op se não suportado).
 */
export async function iniciarOuvinteForeground(): Promise<() => void> {
  if (!firebaseConfigCompleto() || !(await suportaPush())) return () => {};
  if (Notification.permission !== "granted") return () => {};

  try {
    const messaging = getMessaging(getFirebaseApp());
    const unsubscribe = onMessage(messaging, (payload) => {
      window.dispatchEvent(new Event("pauta:notificacoes-atualizadas"));
      const titulo = payload.notification?.title ?? "Pauta";
      const url = telaParaUrl(payload.data);
      const n = new Notification(titulo, {
        body: payload.notification?.body,
        icon: "/favicon.ico",
        data: { url },
      });
      n.onclick = () => {
        window.focus();
        if (window.location.pathname !== url) window.location.assign(url);
        n.close();
      };
    });
    return unsubscribe;
  } catch {
    return () => {};
  }
}
