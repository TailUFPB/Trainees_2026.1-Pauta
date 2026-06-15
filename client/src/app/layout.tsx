import type { Metadata } from "next";
import { Bricolage_Grotesque, Geist, Geist_Mono } from "next/font/google";
import { LoginModalProvider } from "@/components/auth/LoginModalProvider";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
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
  return (
    <html
      lang="pt-BR"
      className={`${bricolage.variable} ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlashThemeScript }} />
      </head>
      <body className="min-h-full flex flex-col bg-bg text-text" suppressHydrationWarning>
        <a href="#main-content" className="skip-link">
          Pular pro conteúdo principal
        </a>
        <LoginModalProvider>
          <SiteHeader />
          <main id="main-content" className="flex-1">
            {children}
          </main>
          <SiteFooter />
        </LoginModalProvider>
      </body>
    </html>
  );
}
