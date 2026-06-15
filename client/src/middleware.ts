import { createServerClient } from "@supabase/ssr";
import { NextRequest, NextResponse } from "next/server";

// Rotas que dispensam autenticação: landing, fluxo de auth e estáticos.
// O matcher abaixo já filtra /_next/static, /_next/image, favicon.ico, *.svg e *.png
// antes mesmo do middleware rodar. Não adicione padrões de imagem aqui — `/conta/foto.jpg`
// não deve virar pública por acidente.
const ROTAS_PUBLICAS: RegExp[] = [
  /^\/$/,                         // landing
  /^\/auth\//,                    // /auth/callback etc.
  /^\/feed(\/|$)/,                // feed público
  /^\/mapa(\/|$)/,                // mapa público
  /^\/candidatos(\/|$)/,          // candidatos público
  /^\/problemas(\/|$)/,           // detalhe público de problema
];

function ehPublica(pathname: string): boolean {
  return ROTAS_PUBLICAS.some((re) => re.test(pathname));
}

export async function middleware(request: NextRequest) {
  // O service worker do Firebase faz importScripts() de domínios externos.
  // Aplicar a CSP estrita (ou o redirect de auth) aqui quebraria o push.
  if (request.nextUrl.pathname === "/firebase-messaging-sw.js") {
    return NextResponse.next();
  }

  // Nonce por request — Next aplica automaticamente aos seus próprios <script>
  // desde que a CSP com o nonce esteja também no header da REQUEST encaminhada.
  const nonce = btoa(crypto.randomUUID());
  const isProd = process.env.NODE_ENV === "production";
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isProd ? "" : " 'unsafe-eval'"}`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob: https:`,
    `font-src 'self' data:`,
    `connect-src 'self' https://*.googleapis.com`,
    `worker-src 'self'`,
    `frame-ancestors 'none'`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    ...(isProd ? [`upgrade-insecure-requests`] : []),
  ]
    .join("; ")
    .replace(/\s{2,}/g, " ")
    .trim();

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("content-security-policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("content-security-policy", csp);
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            request.cookies.set(name, value);
            response.cookies.set(name, value, {
              ...options,
              httpOnly: true,
              secure: process.env.NODE_ENV === "production",
              sameSite: "lax",
              path: "/",
            });
          });
        },
      },
    },
  );
  const { data: { user } } = await supabase.auth.getUser();
  const { pathname } = request.nextUrl;

  // Usuário logado na landing → manda direto pro dashboard.
  if (user && pathname === "/") {
    return NextResponse.redirect(new URL("/conta", request.url));
  }

  // Rota privada sem sessão → landing com modal de login + redirect ao destino.
  if (!user && !ehPublica(pathname)) {
    const url = new URL("/", request.url);
    url.searchParams.set("login", "1");
    url.searchParams.set("redirectTo", pathname);
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.svg$|.*\\.png$).*)",
  ],
};
