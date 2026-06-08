import { createServerClient } from "@supabase/ssr";
import { NextRequest, NextResponse } from "next/server";

// Rotas que dispensam autenticação: landing, fluxo de auth e estáticos.
const ROTAS_PUBLICAS: RegExp[] = [
  /^\/$/,                         // landing
  /^\/auth\//,                    // /auth/callback etc.
  /^\/_next\//,                   // estáticos do Next
  /^\/.*\.(png|svg|jpg|jpeg|webp|ico)$/,
];

function ehPublica(pathname: string): boolean {
  return ROTAS_PUBLICAS.some((re) => re.test(pathname));
}

export async function middleware(request: NextRequest) {
  const response = NextResponse.next({ request });
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
            response.cookies.set(name, value, options);
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
