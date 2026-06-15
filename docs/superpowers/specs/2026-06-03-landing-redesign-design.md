# Landing Redesign — Design Spec

**Data:** 2026-06-03
**Projeto:** Pauta — plataforma de transparência política municipal (Paraíba)
**Escopo:** Redesenhar a home (`/`) como uma landing page de qualidade premium, com login modal integrado, sistema de componentes reusáveis, e animações elegantes que carregam em qualquer dispositivo. Front em Next.js 16 + React 19 + Tailwind 4 + Supabase, com React Compiler habilitado.

---

## 1. Decisões de produto (norteadoras)

| Decisão | Escolha |
|---|---|
| Público primário | Cidadão indignado — ação principal: reportar um problema em 30 segundos |
| Personalidade visual | Cívico-tech moderno (Linear / Vercel / Stripe, com alma cívica) |
| Tratamento do hero | Mapa estilizado animado + headline gigante |
| Estrutura da landing | Storytelling em 4 capítulos abaixo do hero |
| Padrão de login | Modal acionável de qualquer CTA (Google OAuth + magic link) |
| Estado logado da rota `/` | Sempre a landing pública; áreas próprias em rotas dedicadas |
| Tema visual padrão | Light, com toggle pra dark |
| Escopo regional | Paraíba toda (4 cidades: João Pessoa, Bayeux, Santa Rita, Campina Grande) |

---

## 2. Sistema visual

### 2.1 Paleta — Light (padrão)

| Token | Valor | Uso |
|---|---|---|
| `--color-bg` | `#FAFAF7` | Background base (off-white quente) |
| `--color-surface` | `#FFFFFF` | Cards elevados, surfaces |
| `--color-surface-inverted` | `#0A0E1A` | CTA final, footer alternativo |
| `--color-border` | `#E5E7EB` | Borders sutis |
| `--color-border-strong` | `#CBD5E1` | Borders de inputs em foco |
| `--color-text` | `#0A0E1A` | Texto primário (azul-noite quase preto) |
| `--color-text-muted` | `#4B5563` | Texto secundário |
| `--color-accent` | `#FF6B35` | Laranja sinal cívico — CTAs, pontos no mapa, números chave |
| `--color-accent-hover` | `#E55A2A` | Hover do accent |
| `--color-info` | `#1E40AF` | Azul institucional — links, hover sutil |
| `--color-success` | `#10B981` | Verde de problemas resolvidos |
| `--color-danger` | `#DC2626` | Erros, validações |

### 2.2 Paleta — Dark (toggle)

| Token | Valor |
|---|---|
| `--color-bg` | `#0A0E1A` |
| `--color-surface` | `#141828` |
| `--color-border` | `#1F2438` |
| `--color-text` | `#F4F4F0` |
| `--color-text-muted` | `#94A3B8` |
| `--color-accent` | `#FF6B35` (mantém) |

### 2.3 Tipografia

- **Display / headlines:** Geist Sans, weight 700, tracking `-0.02em` em tamanhos ≥40px
- **Body:** Geist Sans, weight 400/500
- **Mono (números, stats, dados):** Geist Mono — números tabulares evitam layout shift
- **Escala fluida (clamp mobile→desktop):**

| Token | Mobile | Desktop |
|---|---|---|
| `text-xs` | 12 | 12 |
| `text-sm` | 14 | 14 |
| `text-base` | 16 | 16 |
| `text-lg` | 17 | 18 |
| `text-xl` | 20 | 22 |
| `text-2xl` | 24 | 28 |
| `text-3xl` | 30 | 40 |
| `text-4xl` | 38 | 56 |
| `text-display` | 48 | 72 |
| `text-hero` | 56 | 96 |

- Line-height: 1.5 para body, 1.1 para display, 1.3 para headings intermediários

### 2.4 Espaçamento, raio, sombra

- Escala 4/8: `4, 8, 12, 16, 24, 32, 48, 64, 96, 128`
- Radius: `sm 6 · md 10 · lg 16 · pill 999`. Cards e modais usam `lg`.
- Sombras (3 níveis):
  - `shadow-1` (hover sutil): `0 1px 2px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.06)`
  - `shadow-2` (modal): `0 10px 30px rgba(15,23,42,.10), 0 4px 12px rgba(15,23,42,.08)`
  - `shadow-3` (popover/menu): intermediário entre 1 e 2
- Em dark mode: sombras viram "glow" suave + border interna mais visível

### 2.5 Motion budget

| Variável | Valor |
|---|---|
| `--motion-fast` | `150ms` (micro-interações: hover, foco) |
| `--motion-base` | `250ms` (entradas padrão, transições UI) |
| `--motion-slow` | `400ms` (transições de página, modais) |
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Stagger entre itens de lista | `40ms` |

- **Library:** `motion` (framer-motion v12) — tree-shakeable, suporta React 19 + React Compiler
- **Regras universais:**
  - Toda animação respeita `prefers-reduced-motion` (fallback: fade opacity 100ms ou nada)
  - Anima apenas `transform` e `opacity`. Nunca `width`, `height`, `top`, `left`
  - Entrada de seções via IntersectionObserver — só anima ao entrar na viewport
  - Frame budget de 16ms — máximo 2 elementos animando simultaneamente no hero

### 2.6 Tokens em código

- `client/src/lib/design/tokens.ts` — const TS exportando todos os tokens (autocompletável, type-safe)
- `client/src/lib/design/motion.ts` — presets de motion (fadeUp, stagger, slideIn, pulse)
- `client/src/app/globals.css` — Tailwind 4 lê via `@theme inline { ... }` apontando pra CSS vars
- Dark mode controlado por `[data-theme="dark"]` no `<html>` (sem flash via script bloqueante mínimo no `<head>`)

---

## 3. Arquitetura de componentes

### 3.1 Estrutura de pastas

```
client/src/
├── app/
├── lib/
│   ├── design/
│   │   ├── tokens.ts
│   │   └── motion.ts
│   └── hooks/
│       ├── useReducedMotion.ts
│       ├── useInView.ts
│       └── useTheme.ts
└── components/
    ├── primitives/      # blocos atômicos, sem regra de negócio
    │   ├── Button.tsx
    │   ├── Container.tsx
    │   ├── Section.tsx
    │   ├── Eyebrow.tsx
    │   ├── Heading.tsx
    │   ├── Stat.tsx
    │   ├── Card.tsx
    │   ├── Badge.tsx
    │   ├── Modal.tsx
    │   └── ThemeToggle.tsx
    ├── motion/          # wrappers de motion reusáveis
    │   ├── FadeUp.tsx
    │   ├── StaggerChildren.tsx
    │   └── CountUp.tsx
    ├── layout/
    │   ├── SiteHeader.tsx
    │   ├── SiteFooter.tsx
    │   └── MobileNav.tsx
    ├── landing/         # exclusivo da landing
    │   ├── Hero.tsx
    │   ├── StylizedMap.tsx
    │   ├── HowItWorks.tsx
    │   ├── ImpactStats.tsx
    │   ├── CandidatesTeaser.tsx
    │   └── FinalCTA.tsx
    └── auth/
        ├── LoginModal.tsx
        └── AuthGate.tsx
```

### 3.2 Princípios

- **Camadas só descem:** `primitives/` nunca importa de `landing/`, `auth/`, ou `layout/`
- **Server-first:** Server Components por padrão. `"use client"` só em: `LoginModal`, `ThemeToggle`, `CountUp`, `MobileNav`, `StylizedMap`, `MapaProblemas` (em /mapa)
- **Variantes via `cva`** (class-variance-authority) — autocompleta e casa com Tailwind
- **Props sempre tipadas** no topo do arquivo, sem `any`
- **React Compiler habilitado** — não escrevemos `useMemo`/`useCallback` manuais

### 3.3 API dos primitives principais

**`Button`**
- Variants: `primary` (accent sólido) · `secondary` (border + texto) · `ghost` (só texto + hover)
- Sizes: `sm` (32) · `md` (40) · `lg` (52)
- Props: `loading`, `disabled`, `asChild` (Radix Slot — pra virar `<Link>` sem perder estilo)
- Touch target mínimo 44×44 sempre (padding compensa em `sm`)

**`Section`**
- Padding vertical consistente (`py-16 md:py-24`)
- Aceita prop `inView` (default true) — envolve filhos em `FadeUp`
- `aria-labelledby` opcional

**`Stat`**
- Número grande em mono + label pequeno embaixo + tendência opcional
- Anima via `CountUp` se prop `animate` (default true), respeitando reduced-motion

**`Modal`**
- Base: Radix `Dialog` (foco trap, ESC, click-fora)
- Mobile: vira bottom sheet (slide up + swipe-down dismiss)
- Desktop: centralizado + scrim 60% black + scale-in 250ms

---

## 4. Landing seção a seção

### 4.1 Hero

**Layout:**
- Desktop: 2 colunas 1.1fr/1fr, gap 64px
- Mobile: stack vertical, mapa abaixo do texto, headline `clamp(48px, 12vw, 72px)`

**Coluna esquerda:**
- `Eyebrow` "Plataforma cívica para a Paraíba"
- `Heading h1` display: "Veja o que a sua rua precisa. **Cobre quem decide.**" (segundo período com `--color-accent`)
- `p` 18px muted: "Mapeie problemas de infraestrutura em João Pessoa, Bayeux, Santa Rita e Campina Grande. Descubra quais vereadores defendem suas pautas."
- 2 `Button`s: primário "Reportar um problema" (envolto em `AuthGate redirectTo="/reportar"`) + secundário "Ver o mapa da Paraíba" (link direto `/mapa`)

**Coluna direita — `StylizedMap`:**
- SVG inline do contorno da Paraíba (viewBox fixo, ~aspect 1.4)
- 4 pontos coloridos pulsando nos pólos: JP, Bayeux, SR, CG
- Pulse via `@keyframes` CSS (sem JS) — scale 1→1.4 + opacity 1→0 em 2s, infinite
- Cada ponto com delay diferente (0, 0.5s, 1s, 1.5s) — pulse não sincronizado
- Linhas de calor sutis (path com `stroke-opacity` baixa) ligando os pólos
- Em mobile, mapa abaixo, max-h 280px, mesmas animações

### 4.2 Capítulo 1 — "Como funciona"

- `Section` com `Eyebrow` "Em 3 passos" + `Heading h2` "Reportar é mais rápido que reclamar no grupo da família"
- 3 `Card`s em grade (1 col mobile, 3 col desktop), com `StaggerChildren`:
  1. **Reporte em 30s** — Lucide `Camera` — "Foto + GPS. A IA classifica o tipo e a severidade."
  2. **A cidade vê** — Lucide `MapPin` — "Seu problema entra no mapa público, junto com os vizinhos."
  3. **Quem decide é avisado** — Lucide `Bell` — "Vereadores e ONGs recebem alertas dos problemas da sua região."

### 4.3 Capítulo 2 — "Impacto"

- `Section` com `Eyebrow` "Por enquanto" + `Heading h2` "Já estamos cobrindo:"
- 3 `Stat`s grandes em linha (stack no mobile):
  - `847` problemas reportados
  - `142` resolvidos
  - `4` cidades cobertas
- Abaixo, grade 2×3 (mobile: 1×3 com scroll horizontal opcional) de "últimos resolvidos": cada card pequeno com foto thumb + bairro + tempo desde resolução
- Dados vêm do backend (rota nova `GET /api/v1/landing/stats` no FastAPI) ou hardcoded inicialmente se ainda não houver dados reais — neste segundo caso, marcar com comentário `// TODO: trocar por fetch quando endpoint existir` (a decisão fica no plano)

### 4.4 Capítulo 3 — "Feche o ciclo"

- `Section` 2 colunas
- Esquerda: `Eyebrow` "Recomendação por afinidade" + `Heading h2` "Saiba quem realmente defende suas pautas" + sub + `Button` secundário "Ver minhas recomendações" (envolto em `AuthGate redirectTo="/recomendacoes"`)
- Direita: stack vertical de 2-3 cards de candidato (foto circular + nome + cargo + barra de match %)
- Cards têm hover sutil (translate Y -2px + sombra)

### 4.5 Capítulo 4 — CTA Final

- `Section` com `--color-surface-inverted` (escuro mesmo em light mode, pra contraste forte)
- Centralizado: `Heading h2` "Sua cidade não precisa esperar a próxima eleição." + `Button` primário grande "Comece a reportar agora" (envolto em `AuthGate`)
- Subtexto pequeno embaixo: "Grátis. Anônimo se você preferir."

### 4.6 Footer

- 3 colunas (1 col mobile)
- Sobre (parágrafo curto de missão)
- Cidades cobertas (lista)
- Links (Privacidade, GitHub, Contato)
- `ThemeToggle` discreto no canto inferior direito
- Linha de copyright

---

## 5. Sistema de login

### 5.1 Componente `LoginModal`

**Estrutura:**
- `Modal` (base Radix Dialog) com largura ~440px
- `Heading h3` "Entre pra reportar e acompanhar" (contextualiza o porquê)
- `Button` primário grande "Continuar com Google" (com ícone Google) → `supabase.auth.signInWithOAuth({ provider: 'google' })`
- Divisor "ou" (linha + texto centralizado)
- `<form>` com:
  - Input email rotulado
  - `Button` secundário "Enviar link mágico" → `supabase.auth.signInWithOtp({ email })`
- Estado de sucesso (após magic link): substitui form por mensagem "Confira seu e-mail" + ícone check + botão "Fechar"
- Footer pequeno: "Ao continuar, você concorda com [Termos] e [Privacidade]"

**Estados gerenciados:**
- `idle` (form padrão) · `loading-oauth` · `loading-magic` · `success-magic` · `error`
- Loading desabilita os botões e mostra spinner inline
- Erros aparecem em `<div role="alert">` acima do divisor

**Mobile:**
- Vira bottom sheet — slide up 400ms, swipe-down dismiss
- Largura full
- Foco no primeiro botão ao abrir

### 5.2 Componente `AuthGate`

```tsx
<AuthGate redirectTo="/reportar">
  <Button>Reportar um problema</Button>
</AuthGate>
```

**Comportamento:**
- Lê sessão Supabase via hook `useSession` (client-side, pra reagir a login sem reload)
- **Deslogado:** intercepta clique → grava `redirectTo` em `sessionStorage` → abre `LoginModal` via context
- **Logado:** delega click direto pro filho (Link normal)
- Funciona com qualquer filho que aceite `onClick` (Button, Link)

### 5.3 Provider e contexto

- `LoginModalProvider` no `RootLayout` — gerencia abertura global
- `useLoginModal()` hook expõe `open()`, `close()`, `isOpen`
- Modal renderiza no root via portal Radix
- Após login bem-sucedido, `useSession` detecta a mudança → modal fecha → lê `redirectTo` do `sessionStorage` → navega

### 5.4 Middleware de auth

- `client/src/middleware.ts` mantém a sessão Supabase atualizada em cada request (já é o padrão `@supabase/ssr`)
- Rotas `/mapa`, `/reportar`, `/recomendacoes` ficam acessíveis sem auth (a landing convida, não bloqueia leitura)
- Mas POST de reportar problema valida `user` no backend (já é o caso)

---

## 6. Performance e estratégia de motion

### 6.1 Imagens

- `next/image` em todas as fotos (já tem `remotePatterns` configurado)
- WebP/AVIF automático via Next
- Mapa estilizado = **SVG inline** (zero requests, escala perfeito, anima via CSS puro)
- Fotos de candidato/problemas: `loading="lazy"` abaixo do hero, `width`/`height` declarados sempre

### 6.2 Fontes

- Geist via `next/font/google` (já tá) — `display: swap` automático
- Preload só de Geist Sans 400 e 700
- Geist Mono carregado quando o componente Stat aparece (ou via subset on-demand)

### 6.3 JS bundle

- Server Components por padrão
- Client Components: lista canônica em §3.2
- `motion` (framer-motion v12) importado dinamicamente nos wrappers `FadeUp`/`StaggerChildren`/`CountUp`
- `leaflet` + `react-leaflet` permanecem isolados em `/mapa`, fora do bundle de `/`
- **Alvo: First Load JS de `/` < 100KB**

### 6.4 Motion robusto

- **IntersectionObserver** para entrada de seções (não anima fora da viewport)
- **`prefers-reduced-motion`:**
  - Contadores mostram valor final direto
  - Entrances viram `opacity` 100ms (ou nada)
  - Pulse do mapa para
  - Stagger removido
- **Mobile <375px:** stagger reduzido pela metade, pulse do mapa simplificado (sem linhas de calor)
- **Frame budget de 16ms** — máximo 2 elementos animando juntos no hero

### 6.5 Core Web Vitals — alvos

| Métrica | Alvo |
|---|---|
| LCP | < 2.0s |
| CLS | < 0.05 |
| INP | < 100ms |
| TBT | < 200ms |

### 6.6 React Compiler

- Habilitar `experimental.reactCompiler: true` em `next.config.ts`
- Significa: zero `useMemo`/`useCallback` manuais nos componentes da landing
- Componentes ficam mais limpos e o compiler memoriza automaticamente

---

## 7. Estado logado + header dinâmico

### 7.1 `SiteHeader` (Server Component)

- Lê sessão Supabase via `@supabase/ssr` no servidor
- Renderiza variante deslogado ou logado

**Deslogado:**
- Logo Pauta (link `/`)
- Nav: Mapa · Reportar · Candidatos
- À direita: `Button` "Entrar" (`ghost`) → abre `LoginModal`

**Logado:**
- Logo
- Nav
- À direita: avatar com menu dropdown (Radix DropdownMenu)
  - Minha área (`/minha-area` — fora do escopo desta spec; placeholder)
  - Configurações
  - Sair (`supabase.auth.signOut()`)

**Sem flash:** renderização no server → entrega já com o estado correto. Middleware mantém cookies em dia.

### 7.2 Mobile nav

- `MobileNav` substitui a nav central em viewports <768px
- Trigger: botão hambúrguer no header
- Drawer lateral (Radix Dialog em variante side) com nav + login/avatar

### 7.3 Landing estável

- A landing inteira é **idêntica** entre logado/deslogado
- Só o `SiteHeader` e o comportamento dos `AuthGate`s mudam
- Zero re-render de seção, zero flicker

---

## 8. Acessibilidade (checklist crítico)

- Contraste WCAG AA mínimo (texto 4.5:1, UI 3:1) — paleta calibrada pra isso em ambos os temas
- Foco visível em todos os interativos (`focus-visible:ring-2 ring-accent ring-offset-2`)
- Headings hierárquicos sem pular nível
- Alt em todas as imagens significativas; `aria-hidden` em decorativas
- Touch target mínimo 44×44 em todos os interativos
- Modal: foco trap + retorna foco ao gatilho ao fechar
- Toast/erros: `role="alert"` ou `aria-live="polite"`
- Suporta zoom 200% sem quebra
- `prefers-reduced-motion` respeitado em toda animação
- Skip link "Pular pro conteúdo principal" no início do `<body>`

---

## 9. Fora de escopo (não fazer nesta spec)

- Reescrever as rotas `/mapa`, `/reportar`, `/recomendacoes` — só atualizam o header global e ganham acesso aos `primitives/` (refactor pontual permitido, redesign completo não)
- Dashboard "Minha área" pós-login — placeholder no menu, conteúdo é outra spec
- Backend novo (`/api/v1/landing/stats`) — se ainda não houver dados reais, usar mock estático no front, com TODO no código
- Internacionalização (PT-BR fixo)
- Cookie banner / consent (assumir fora de escopo do MVP)

---

## 10. Critérios de aceitação

A spec se considera entregue quando:

1. Rodando `npm run dev` na `client/`, `/` renderiza a landing nova com todas as seções: hero + 4 capítulos (Como funciona, Impacto, Feche o ciclo, CTA Final) + footer
2. Modal de login abre clicando em qualquer CTA protegido (deslogado), Google OAuth e magic link funcionam contra Supabase
3. Após login, modal fecha e usuário é redirecionado pra rota pretendida
4. Header muda entre estados deslogado/logado sem flash
5. Toggle de tema funciona, persiste em `localStorage`, sem flash de tema errado no reload
6. Lighthouse mobile (slow 4G simulado) na rota `/`: Performance ≥ 90, Accessibility = 100, Best Practices ≥ 95, SEO ≥ 95
7. `prefers-reduced-motion` desliga as animações principais (mapa, contadores, entradas)
8. Funciona sem erro visual em viewports 360px, 768px, 1024px, 1440px
9. Zero `any`, zero `useMemo`/`useCallback` manuais, zero HTML repetido (tudo via `primitives/`)
10. `npm run lint` e `npm run build` passam limpos

---

## 11. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Mapa SVG da Paraíba pode ficar pesado (path complexo) | Simplificar via `svgo` agressivo; usar contorno baixa-poly (~200 vértices) — perde detalhe mas mantém legibilidade |
| `framer-motion` adiciona bundle | Importar via `motion/react` (v12 tree-shakeable). Se ainda pesado, fallback CSS-only para entrances (perde stagger sofisticado mas funciona) |
| React Compiler ainda é experimental em Next 16 | Já é estável o suficiente em React 19. Se quebrar build, desativar temporariamente — código não depende dele, apenas se beneficia |
| Dados reais (847 problemas etc) podem não existir no MVP | Mock estático com TODO. Não bloqueia entrega visual |
| Dark mode pode ter regressões em algum primitive | Storybook leve via páginas internas `/dev/*` (opcional) ou checklist manual nas seções |
