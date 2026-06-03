# Fatia 1 — "Minha Pauta": área logada + Meus Reportes + endurecimento de privacidade

**Data:** 2026-06-03
**Status:** spec aprovado, aguardando plan

## 1. Contexto e propósito

Hoje o front do Pauta tem login funcional (Supabase Auth via Google e magic link), mas
o login praticamente não destrava nada do ponto de vista do usuário. O cidadão consegue
reportar um problema e cadastrar interesses pra recomendação de vereadores, mas:

- Não consegue **acompanhar** o que reportou (status atual, evolução, histórico).
- Não tem **lar logado** — nenhum painel, dashboard ou hub.
- O dropdown da conta tem só um destino útil ("Minhas recomendações").
- Existe uma página `/login` que serve apenas como stub pra reabrir o modal.

A landing promete *"sua cidade não precisa esperar a próxima eleição"* e *"cobre quem
decide"*, sugerindo engajamento contínuo. O produto entregue não materializa essa
promessa porque não há ciclo de retorno.

Além disso, o backend hoje expõe `autor_id` em todo `GET /problemas` e `GET /problemas/{id}`
— qualquer um vê quem reportou o quê. E `PATCH /problemas/{id}/status` aceita qualquer
usuário logado mexer no status de qualquer reporte (buraco de segurança).

Esta fatia constrói o lar do usuário logado, entrega valor imediato ("acompanhe o que
você reportou"), corrige a exposição pública de PII, fecha o buraco do PATCH, e
prepara o terreno pra as fatias 2 (seguir vereadores/regiões) e 3 (notificações).

## 2. Escopo

### Entra na Fatia 1

1. Shell autenticado em `/conta` com sub-navegação preparada pra crescer.
2. Lista "Meus Reportes" em `/conta/reportes` com filtro por status e paginação.
3. Detalhe de um reporte em `/conta/reportes/[id]` (acesso restrito ao autor).
4. Ações no detalhe: **cancelar próprio reporte** / **marcar próprio reporte como resolvido**.
5. Remoção da rota `/login` redundante.
6. Dropdown do header revisado (avatar, atalhos para Meus Reportes / Recomendações / Sair).
7. Empty state pra usuário com 0 reportes.
8. **Backend:** endpoint novo `GET /usuarios/me/problemas`.
9. **Backend:** restrição de `PATCH /problemas/{id}/status` — só autor age sobre próprio
   reporte, com transições limitadas.
10. **Backend:** remoção de `autor_id` e `descricao` da resposta pública de
    `GET /problemas` e `GET /problemas/{id}` para não-autores.
11. **Schema:** remoção das colunas `users.nome` e `users.email` (PII redundante; email
    vem do JWT da sessão).
12. **RLS:** habilitar Row Level Security em `users`, `problemas`, `inscricoes`,
    `seguidores_politico`, `eventos_outbox`, `politicos` com policies adequadas.
    Backend continua usando role com `BYPASSRLS` (documentado).

### Não entra (roadmap para fatias futuras)

- **Cifragem at-rest com `pgcrypto`** — vai para Fatia 4 "Privacidade & Compliance".
  Decisão pendente: gerenciamento de chave (env vs. Supabase Vault vs. KMS externo).
- **Seguir vereadores e regiões** — Fatia 2.
- **Notificações in-app e feed** — Fatia 3. Bloqueada por: definir consumidor do
  `eventos_outbox` (Node/Python — decisão de time aberta).
- **Histórico/log estruturado de mudanças de status** — Fatia 3.
- **Moderação / roles operacionais (em_atendimento, arquivado por staff)** — fora.

## 3. Arquitetura de rotas e shell

### Rotas novas (frontend)

| Rota | Acesso | Conteúdo |
|---|---|---|
| `/conta` | logado | redirect server-side pra `/conta/reportes` |
| `/conta/reportes` | logado | lista "Meus Reportes" |
| `/conta/reportes/[id]` | logado, só autor | detalhe + ações no próprio reporte |

### Rotas removidas

- `/login` — apaga `client/src/app/login/page.tsx`. CTAs de login passam a abrir o
  modal diretamente. `/auth/callback` continua (endpoint do Supabase) e redireciona
  pra `/conta/reportes` por default (ou para `redirectTo` se vier do modal).

### Shell `/conta`

- `client/src/app/conta/layout.tsx` é server component que:
  - Valida sessão via `getServerUser()`. Se ausente, `redirect('/?login=1')`.
  - Renderiza header normal + sub-navegação leve no topo (tabs: "Meus Reportes" /
    "Recomendações" / link "Sair").
- A sub-navegação é projetada para crescer:
  - Fatia 2 acrescenta "O que sigo".
  - Fatia 3 acrescenta "Notificações" com badge.

### AuthGate

Continua usando o `AuthGate` existente (`client/src/components/auth/AuthGate.tsx`) para
abrir o modal quando usuário não-logado clica em CTA gateado. Sem mudanças nessa camada.

### Detalhe: página dedicada (não drawer)

`/conta/reportes/[id]` é página full — URL compartilhável, deep-link trivial, sem
complexidade de estado de drawer. UI fica a cargo da execução com `ui-ux-pro-max`.

## 4. Backend

### Endpoint novo

```
GET /usuarios/me/problemas
  Query params:
    status?: aberto | em_atendimento | resolvido | arquivado | cancelado  (repetível)
    limite: int = 20 (max 100)
    offset: int = 0
  Resposta: list[ProblemaOut]  (ordenado por created_at DESC)
  Auth: get_current_user obrigatório
  WHERE autor_id = current_user.id
```

### Endpoint alterado — `PATCH /problemas/{id}/status`

**Hoje:** aceita qualquer status, sem checar autoria → buraco de segurança.

**Novo:**

- Retorna **403** quando `problema.autor_id != current_user.id`.
- Transições permitidas pro autor:
  - `aberto → cancelado`
  - `aberto → resolvido`
  - `em_atendimento → resolvido`
- Bloqueado pro autor (operacionais, ficam pra role-based em outra fatia):
  `em_atendimento`, `arquivado`.
- Transições inválidas retornam **422**.
- `resolvido_por` (campo livre hoje) passa a ser preenchido automaticamente com o
  email do autor (do JWT) quando status vai pra `resolvido` por ação do cidadão.

### Endpoints alterados — exposição pública

- `GET /problemas` (lista para o mapa) e `GET /problemas/{id}` (detalhe) param de
  retornar `autor_id` e `descricao` para não-autores.
- Cria-se schema `ProblemaPublicoOut` (sem `autor_id`, sem `descricao`).
- `ProblemaOut` (completo) é devolvido em:
  - `GET /usuarios/me/problemas` (sempre — só lista próprios).
  - `GET /problemas/{id}` **quando o solicitante autenticado é o autor**.
- Implementação: `GET /problemas/{id}` aceita Authorization opcional. Hoje o
  backend só tem `get_current_user` (obrigatório); esta fatia introduz
  `get_current_user_optional` em `server/app/core/auth.py` — retorna `User | None`
  conforme presença e validade do header. Se houver sessão e
  `user.id == problema.autor_id`, devolve `ProblemaOut`; senão devolve
  `ProblemaPublicoOut`.

### Schema — migration "remove PII de users"

- `ALTER TABLE users DROP COLUMN nome;`
- `ALTER TABLE users DROP COLUMN email;`
- Atualiza `server/app/core/auth.py::get_current_user` — upsert não preenche mais
  `email` nem `nome`.
- Atualiza `server/app/routers/usuarios.py`:
  - `UsuarioOut` perde `nome` e `email`.
  - `me` deixa de devolver esses campos.
- Front passa a ler `email` do `session.user` do Supabase (já disponível via
  `useSession()` no client e `getServerUser()` no server) — não precisa request extra.

### Schema — migration "RLS + view pública"

- `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` em: `users`, `problemas`, `inscricoes`,
  `seguidores_politico`, `eventos_outbox`, `politicos`.
- Policies (todas via `auth.uid()` do Supabase, com cast `::uuid` quando necessário —
  a confirmar na execução, item de verificação):
  - `users`: `SELECT, UPDATE` quando `id = auth.uid()`.
  - `inscricoes`, `seguidores_politico`: `SELECT, INSERT, DELETE` quando
    `user_id = auth.uid()`.
  - `eventos_outbox`: **DENY ALL** via PostgREST. Só backend e consumidor de outbox
    tocam (ambos com role bypass).
  - `politicos`: `SELECT` público (read-only).
  - `problemas`: `SELECT` permitido só quando `autor_id = auth.uid()`. Para o caso
    público (mapa via PostgREST, se algum dia for usado), cria-se uma **view**
    `problemas_publica` (sem `autor_id`, sem `descricao`) com `SECURITY INVOKER` e
    `GRANT SELECT ... TO anon, authenticated`.
- Backend FastAPI continua via SQLAlchemy direto. **Hoje usa o role `postgres`
  (superuser, bypass implícito).** Documentado no spec; criação de role
  `pauta_api` com `BYPASSRLS` + privilégios mínimos fica como follow-up — não
  bloqueia a fatia mas é preferência forte.

### Por que RLS importa mesmo com o backend não-PostgREST?

O backend Python passa pelo SQLAlchemy direto, então **RLS não afeta** o caminho
principal do app. Mas o **anon key do Supabase vai no bundle do front** — qualquer um
pode pegar e chamar PostgREST diretamente. Sem RLS, esse caminho expõe tudo. Com RLS,
serve como defesa em profundidade: mesmo abusando do anon key, ninguém lê `users`,
`problemas`, `inscricoes` ou `eventos_outbox`. A view `problemas_publica` é o único
ponto de leitura pública via PostgREST, e ela já omite os campos sensíveis.

## 5. Frontend

### Arquivos novos

```
client/src/app/conta/
  layout.tsx            # server, valida sessão, renderiza shell + sub-nav
  page.tsx              # redirect server-side pra /conta/reportes
  reportes/
    page.tsx            # server, fetch inicial de /usuarios/me/problemas
    MeusReportesView.tsx    # client, filtros e paginação
    ReporteCard.tsx         # cartão na lista
    EmptyState.tsx          # estado vazio com CTA pra /reportar
    [id]/
      page.tsx          # server, fetch de /problemas/{id} (versão autor)
      ReporteDetail.tsx     # client, ações + mini-mapa + badges
```

### Arquivos removidos

- `client/src/app/login/page.tsx`
- Qualquer link interno pra `/login` (verificar via grep antes de remover).

### Arquivos alterados

- `client/src/components/layout/HeaderClient.tsx` — dropdown logado:
  - "Meus Reportes" → `/conta/reportes`
  - "Recomendações" → `/recomendacoes`
  - separador
  - "Sair"
- `client/src/components/layout/MobileNav.tsx` — espelha o mesmo.
- `client/src/app/auth/callback/route.ts` — redirect default vira `/conta/reportes`;
  preserva `redirectTo` quando vier do modal.
- `client/src/lib/api/client.ts` — adiciona:
  - `meusProblemas({ status?, limite?, offset? })`
  - `atualizarStatusProblema(id, { status, resolvido_por? })`
- `client/src/lib/api/types.ts` — adiciona `ProblemaPublico` e renomeia/marca
  `Problema` como versão completa (autor). Consumidores do mapa/listagem pública
  passam a tipar `ProblemaPublico`.

### Fluxos principais

**1. Usuário logado vai pra `/conta/reportes`**

- `layout.tsx` valida sessão server-side.
- `page.tsx` faz `GET /usuarios/me/problemas?limite=20&offset=0` com Authorization
  via cookie de sessão.
- Renderiza lista. Filtro de status e paginação são tratados pelo `MeusReportesView`
  client-side via re-fetch.
- Empty state quando lista volta vazia.

**2. Usuário clica num cartão**

- Navega pra `/conta/reportes/{id}`.
- Server fetch `GET /problemas/{id}` com auth — recebe versão completa
  (`ProblemaOut`).
- Renderiza detalhe: mini-mapa (react-leaflet), badges (severidade, status,
  confiança), descrição, foto.
- Se status é `aberto` ou `em_atendimento`: botões "Cancelar reporte" e "Marcar como
  resolvido" disponíveis.
- Clique em ação → `PATCH /problemas/{id}/status` → revalida e mostra novo estado
  (router.refresh() ou re-fetch local).

**3. Usuário não logado tenta `/conta/*`**

- `layout.tsx` detecta ausência de sessão e faz `redirect('/?login=1&redirectTo=/conta/reportes')`.
- `LoginModalProvider` ganha um `useEffect` que lê `searchParams` no mount: se
  `?login=1` está presente, chama `open(redirectTo)`. Hoje o provider só abre via
  chamada explícita do `useLoginModal().open()` — esse comportamento via query param
  é nova capacidade introduzida nesta fatia.

### Estilo

Segue padrão da landing: Bricolage Grotesque, tokens `bg/surface/text/text-muted/accent/danger`,
primitives já existentes (`Card`, `Container`, `Section`, `Eyebrow`, `Heading`, `Badge`,
`Button`). Polimento final dos layouts via `ui-ux-pro-max` na execução.

## 6. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| `auth.uid()` em policy RLS não casa com `users.id` (cast UUID vs text) | Testar policy via psql autenticado antes de commit; item de verificação no plan. |
| Backend hoje usa role `postgres` (bypass implícito). Mudança futura para role sem bypass quebraria queries silenciosamente. | Documentar em `server/.env.example` + README. Não trocar role nesta fatia. |
| Remoção de `users.nome`/`email` quebra consumidor não mapeado. | Grep por `user.nome` e `user.email` no servidor antes da migration. Hoje só `routers/usuarios.py::me` e `core/auth.py::get_current_user` usam. Front usa via Supabase session. |
| Separar `ProblemaPublicoOut` causa duplicação. | Modelos Pydantic com herança; `ProblemaPublicoOut` deriva de uma base e omite campos. |
| View `problemas_publica` + RLS quebra testes de leitura direta. | Testes do backend conectam via SQLAlchemy com role superuser → RLS não interfere. PostgREST não é testado aqui. |
| Primeiro login redireciona para `/conta/reportes` ainda sem reportes. | Empty state coberto com CTA "reportar primeiro problema". |
| Tentativa de cancelar/resolver via curl em reporte de terceiros. | 403 com mensagem clara; teste de backend cobrindo. |
| `descricao` removida da resposta pública pode esconder informação útil para o mapa (ex.: "buraco fundo na esquina"). | Decisão deliberada: descrição livre pode conter PII auto-relatada. Se aparecer demanda real, virar tarefa de Fatia 5 "moderação de conteúdo" — não bloqueia F1. |

## 7. Critérios de sucesso

1. Usuário logado vê em `/conta/reportes` somente os reportes que ele criou, com
   status atual.
2. Usuário logado consegue abrir o detalhe e cancelar ou marcar como resolvido um
   reporte próprio.
3. Usuário não autor recebe `GET /problemas/{id}` sem `autor_id` nem `descricao`
   (verificável via curl).
4. Usuário não autor recebe 403 em `PATCH /problemas/{id}/status` (verificável via
   curl).
5. Tabela `users` no banco não tem mais colunas `nome` nem `email` (verificável via
   `\d users`).
6. RLS habilitado em todas as tabelas listadas (verificável via
   `SELECT relrowsecurity FROM pg_class WHERE relname IN (...)`).
7. SELECT em `problemas` via `anon_key` no PostgREST do Supabase retorna `[]`
   (verificável via curl).
8. SELECT em `problemas_publica` via `anon_key` retorna registros sem `autor_id` nem
   `descricao` (verificável via curl).
9. Rota `/login` retorna 404 (apagada).
10. Dropdown do header logado mostra "Meus Reportes" como entrada principal e leva
    pra `/conta/reportes`.

## 8. Testes

### Backend (pytest, já configurado)

- `test_meus_problemas_lista_apenas_do_autor`
- `test_meus_problemas_filtro_status`
- `test_meus_problemas_paginacao`
- `test_get_problema_publico_oculta_autor_e_descricao`
- `test_get_problema_autor_recebe_tudo`
- `test_patch_status_nao_autor_retorna_403`
- `test_patch_status_autor_transicao_valida`
- `test_patch_status_autor_transicao_invalida_retorna_422`
- `test_users_table_sem_nome_email` (smoke da migration)

### Frontend

Não há framework de teste configurado hoje. O plan vai propor:

- Verificação manual via `make dev` cobrindo os 10 critérios de sucesso.
- Adicionar `vitest` + 2-3 testes de componente fica como follow-up — não bloqueia a fatia.

### RLS

- Script de verificação no plan: curl ao PostgREST do Supabase com `anon_key` em
  cada tabela, conferindo que retorna `[]` ou 401, e que `problemas_publica` é
  acessível e omite os campos certos.

## 9. Migrations

Ordem de aplicação:

1. `XXXX_remove_pii_users.py` — drop colunas `nome` e `email` em `users`.
2. `XXXX_rls_e_view_publica.py` — habilita RLS, cria policies e view
   `problemas_publica`.

## 10. Roadmap das próximas fatias (visão de alto nível)

### Fatia 2 — "Acompanhar"

**Objetivo:** seguir vereadores e regiões para receber alertas direcionados.

**Escopo provável:**

- Backend: 4 endpoints CRUD — `POST/DELETE /usuarios/me/seguidos/politicos/{id}`,
  `POST/DELETE /usuarios/me/regioes` (com geometria de polígono), `GET` para listar
  cada coleção.
- Frontend: botão "Seguir" no card de vereador em `/candidatos`, no detalhe do mapa
  de problemas e na bbox do mapa. Sub-aba "O que sigo" dentro de `/conta`.
- Modelos no banco já existem (`SeguidorPolitico`, `Inscricao` com `regiao`); não
  precisa migration nova.

**Dependências:** nenhuma. Cresce dentro do shell criado na Fatia 1.

### Fatia 3 — "Notificações & Feed"

**Objetivo:** entregar ao usuário um histórico do que aconteceu desde a última visita.

**Escopo provável:**

- Backend: tabela `notificacoes` (ou view materializada sobre `eventos_outbox`) com
  destinatário, lida/não-lida, link.
- Endpoint `GET /usuarios/me/notificacoes` e `POST /usuarios/me/notificacoes/{id}/marcar-lida`.
- Frontend: centro de notificações no header (badge + popover), página
  `/conta/notificacoes` com histórico cronológico.

**Dependências:** decisão de quem consome o `eventos_outbox` (Node vs Python — aberta
no time). Bloqueada por essa definição.

### Fatia 4 — "Privacidade & Compliance"

**Objetivo:** cifragem at-rest de PII que sobrar no DB local + decisões de
gerenciamento de chave.

**Escopo provável:**

- `pgcrypto` com `PGP_SYM_ENCRYPT` em campos de PII que tivermos mantido (a definir).
- Estratégia de chave: env do backend, Supabase Vault ou KMS externo.
- Rotação de chave e procedimento de reencriptação.
- Auditoria de logs e LGPD.

**Dependências:** decisão de produto sobre nível real de garantia exigido (legal,
parcerias com órgãos públicos, etc.).
