/* Service worker do Firebase Cloud Messaging.
   Recebe a config pública por query string (registrado em lib/firebase/push.ts).
   Mantenha a versão dos scripts em sincronia com firebase no package.json. */
importScripts(
  "https://www.gstatic.com/firebasejs/12.14.0/firebase-app-compat.js",
);
importScripts(
  "https://www.gstatic.com/firebasejs/12.14.0/firebase-messaging-compat.js",
);

const params = new URL(self.location).searchParams;
firebase.initializeApp({
  apiKey: params.get("apiKey"),
  authDomain: params.get("authDomain"),
  projectId: params.get("projectId"),
  storageBucket: params.get("storageBucket"),
  messagingSenderId: params.get("messagingSenderId"),
  appId: params.get("appId"),
});

const messaging = firebase.messaging();

// Mesmo mapeamento de tela->rota usado em push.ts (manter em sincronia).
function telaParaUrl(dados) {
  switch (dados && dados.tela) {
    case "mapa":
      return "/mapa";
    case "perfil_politico":
      return "/candidatos";
    default:
      return "/conta/notificacoes";
  }
}

messaging.onBackgroundMessage((payload) => {
  const titulo = (payload.notification && payload.notification.title) || "Pauta";
  self.registration.showNotification(titulo, {
    body: payload.notification && payload.notification.body,
    icon: "/favicon.ico",
    data: { url: telaParaUrl(payload.data), ...payload.data },
  });
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/conta/notificacoes";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((lista) => {
      for (const cliente of lista) {
        if (cliente.url.includes(url) && "focus" in cliente) return cliente.focus();
      }
      return clients.openWindow(url);
    }),
  );
});
