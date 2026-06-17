import type { Metadata } from "next";
import { headers } from "next/headers";
import { Bricolage_Grotesque, Geist, Geist_Mono } from "next/font/google";
import { LoginModalProvider } from "@/components/auth/LoginModalProvider";
import { SessionProvider } from "@/components/auth/SessionProvider";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { getServerUser } from "@/lib/auth/getServerSession";
import { AppShell } from "@/components/layout/AppShell";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
  display: "swap",
  weight: ["600", "700", "800"],
});
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Pauta",
    template: "%s · Pauta",
  },
  description:
    "Mapeie problemas de infraestrutura em João Pessoa, Bayeux, Santa Rita e Campina Grande. Descubra quais vereadores defendem suas pautas.",
};

const noFlashThemeScript = `
(function(){try{
  var t = localStorage.getItem('pauta-theme') || 'light';
  document.documentElement.dataset.theme = t;
}catch(e){
  document.documentElement.dataset.theme = 'light';
}})();
`;

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const user = await getServerUser();
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  return (
    <html
      lang="pt-BR"
      className={`${bricolage.variable} ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        {/* O navegador remove o atributo `nonce` do DOM depois de aplicar a CSP,
            então o valor difere do que o React renderiza no cliente. O script
            continua válido (autorizado pelo nonce); suppressHydrationWarning só
            silencia o falso mismatch de hydration nesse atributo. */}
        <script
          nonce={nonce}
          suppressHydrationWarning
          dangerouslySetInnerHTML={{ __html: noFlashThemeScript }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-bg text-text" suppressHydrationWarning>
        <a href="#main-content" className="skip-link">
          Pular pro conteúdo principal
        </a>
        <SessionProvider
          initialUser={user ? { id: user.id, email: user.email ?? null } : null}
        >
          <LoginModalProvider>
            {user ? (
              <AppShell email={user.email ?? null}>{children}</AppShell>
            ) : (
              <>
                <SiteHeader />
                <main id="main-content" className="flex-1">
                  {children}
                </main>
                <SiteFooter />
              </>
            )}
          </LoginModalProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
