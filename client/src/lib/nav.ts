// Fonte única da navegação do app. Usada por HeaderClient (desktop) e MobileNav
// para evitar arrays duplicados que saíam de sincronia. Itens da conta também
// alimentam o dropdown do header, mantendo rótulos idênticos ao AccountNav.

export interface NavItem {
  href: string;
  label: string;
  /** Quando true, o estado ativo exige igualdade estrita de pathname. */
  exact?: boolean;
}

/** Navegação principal pública — idêntica em desktop e mobile. */
export const NAV_PRINCIPAL: readonly NavItem[] = [
  { href: "/mapa", label: "Mapa" },
  { href: "/reportar", label: "Reportar" },
  { href: "/feed", label: "Feed" },
  { href: "/candidatos", label: "Candidatos" },
];

/** Seção da conta — alimenta o AccountNav e o dropdown do header. */
export const NAV_CONTA: readonly NavItem[] = [
  { href: "/conta", label: "Visão geral", exact: true },
  { href: "/conta/reportes", label: "Meus reportes" },
  { href: "/conta/notificacoes", label: "Notificações" },
  { href: "/conta/configuracoes", label: "Configurações" },
];
