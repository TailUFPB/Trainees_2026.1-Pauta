"use client";
// Configuração do Firebase Web (Cloud Messaging). Todos os valores são públicos
// (chaves NEXT_PUBLIC_*) e precisam apontar para o MESMO projeto Firebase usado
// pelo backend (server/credenciais_firebase.json).
import { getApp, getApps, initializeApp } from "firebase/app";

export const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
} as const;

// Chave pública VAPID (Firebase Console > Cloud Messaging > Web Push certificates).
export const vapidKey = process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY;

/** True quando todas as variáveis obrigatórias para o FCM Web estão presentes. */
export function firebaseConfigCompleto(): boolean {
  return Boolean(
    firebaseConfig.apiKey &&
      firebaseConfig.projectId &&
      firebaseConfig.messagingSenderId &&
      firebaseConfig.appId &&
      vapidKey,
  );
}

/** Inicializa (ou reaproveita) a instância do app Firebase no browser. */
export function getFirebaseApp() {
  return getApps().length ? getApp() : initializeApp(firebaseConfig);
}

/**
 * A config pública serializada como query string, para passar ao service worker
 * (que não enxerga process.env). Mantém o .env como fonte única da verdade.
 */
export function firebaseConfigQuery(): string {
  const params = new URLSearchParams();
  for (const [chave, valor] of Object.entries(firebaseConfig)) {
    if (valor) params.set(chave, valor);
  }
  return params.toString();
}
