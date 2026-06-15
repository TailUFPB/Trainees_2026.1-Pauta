// Fonte única da navegação do app. Usada por HeaderClient (desktop) e MobileNav
// para evitar arrays duplicados que saíam de sincronia. Itens da conta também
// alimentam o dropdown do header, mantendo rótulos idênticos ao AccountNav.

export interface NavItem {
  href: string;
  label: string;
  /** Quando true, o estado ativo exige igualdade estrita de pathname. */
  exact?: boolean;
}

/** Top bar do visitante deslogado — apenas destinos de leitura. */
export const NAV_PUBLICO: readonly NavItem[] = [
  { href: "/feed", label: "Feed" },
  { href: "/mapa", label: "Mapa" },
  { href: "/candidatos", label: "Candidatos" },
];

/** Sidebar do app (usuário logado) — destinos primários, incl. ações. */
export const NAV_APP: readonly NavItem[] = [
  { href: "/feed", label: "Feed" },
  { href: "/mapa", label: "Mapa" },
  { href: "/reportar", label: "Reportar" },
  { href: "/candidatos", label: "Candidatos" },
];

/** Seção da conta — alimenta o AccountNav e o dropdown do header. */
export const NAV_CONTA: readonly NavItem[] = [
  { href: "/conta", label: "Visão geral", exact: true },
  { href: "/conta/reportes", label: "Meus reportes" },
  { href: "/conta/notificacoes", label: "Notificações" },
  { href: "/conta/configuracoes", label: "Configurações" },
];
