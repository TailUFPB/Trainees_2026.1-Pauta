# Verificação Manual — Fatia 2 (Timeline + Cifra do Autor)

Data: 2026-06-08
Branch: `feat/fatia-2-timeline-cifra`

Este roteiro cobre o smoke test ponta-a-ponta da Fatia 2: login wall via
middleware, dashboard `/conta`, composer de publicações com toggle anônimo, e
feed unificado. Tudo o que dá pra checar via teste automatizado já está coberto
pelo `pytest` (87 PASSED) e `npm run lint` / `tsc --noEmit`. Aqui mora o que só
um humano consegue confirmar olhando.

## Pré-requisitos

- `make doctor` precisa estar verde (docker, uv, node>=20, npm, server/.env,
  client/.env.local, AUTOR_CIFRA_KEY, AUTOR_LOOKUP_KEY, SUPABASE_URL).
- Banco do Supabase precisa estar acessível com as credenciais em
  `server/.env` (ou banco local rodando via `make db-up`).
- Nada importante rodando nas portas 3000 / 8000.

## Subir o ambiente

```bash
make dev
```

Espere o server logar `Uvicorn running on http://127.0.0.1:8000` e o client
logar `✓ Ready in …`. Os logs ficam misturados — Ctrl+C para tudo.

## Roteiro

### 1. Login wall protege rotas privadas (deslogado)

Abra uma janela **anônima/incógnita** (sem cookies do Supabase).

1. Vá em `http://localhost:3000/mapa`
   - **Esperado:** redirect imediato para `/?login=1&redirectTo=%2Fmapa`. A
     landing aparece com o modal de login aberto.

2. Vá em `http://localhost:3000/conta/feed`
   - **Esperado:** redirect para `/?login=1&redirectTo=%2Fconta%2Ffeed`.

3. Vá em `http://localhost:3000/conta`
   - **Esperado:** redirect para `/?login=1&redirectTo=%2Fconta`.

4. Vá em `http://localhost:3000/` (sem query string)
   - **Esperado:** landing carrega normalmente. Sem modal aberto.

### 2. Login

Use o método disponível (magic link ou Google). Depois do callback:

- **Esperado:** redirect para `/conta` (dashboard).
- A página mostra: saudação com nome público + 3 cards de stats
  (meus reportes, minhas publicações, resolvidos). Os números podem ser zero —
  o importante é que renderiza sem fallback de erro.

> Se o dashboard ficar travado em "carregando" ou os cards aparecerem todos
> zerados sem motivo: confira `console.error` do servidor Next — agora
> `buscarStats` loga falhas (Item C deste task), antes silenciava.

### 3. Feed: composer público

1. Clique em "Feed" no nav (ou abra `/conta/feed`).
   - **Esperado:** página mostra o composer no topo e ou os cards já existentes
     ou o empty state ("Nada por aqui ainda. Seja o primeiro a publicar.").

2. No composer:
   - Digite `Teste publicação Fatia 2`.
   - **Deixe** o checkbox "Publicar anônimo" desmarcado.
   - Clique em "Publicar".
   - **Esperado:** card novo aparece no topo da lista, com seu nome público
     em vez de "Anônimo".

### 4. Feed: composer anônimo

1. No composer:
   - Digite `Reporte anônimo de teste`.
   - **Marque** o checkbox "Publicar anônimo".
   - Clique em "Publicar".
   - **Esperado:** card aparece no topo com badge "Anônimo" e SEM nome do
     autor. O avatar mostra `?` como inicial.

### 5. Feed: validação client-side de whitespace

1. Tente enviar uma publicação com apenas espaços (`"   "`):
   - **Esperado:** o backend recusa com 422 (Item E). O composer deve mostrar
     erro ao invés de criar publicação fantasma. (Se o front nem habilitar o
     botão por causa de `trim()`, melhor ainda — em qualquer caso, não deve
     virar 500.)

### 6. Problemas: criar via curl (rota anônima)

A UI do `/reportar` ainda não expõe o checkbox `anonimo` (fica pra futura
fatia). Pra confirmar que o backend continua aceitando reportes anônimos com
a cifra do autor:

```bash
# pegar token do navegador depois do login: DevTools > Application > Cookies
# > sb-…-auth-token (o JSON inteiro). Extraia o access_token.
TOKEN="<cole o access_token aqui>"

curl -X POST http://localhost:8000/problemas \
  -H "Authorization: Bearer $TOKEN" \
  -F "lat=-23.55" \
  -F "lng=-46.63" \
  -F "tipo=outro" \
  -F "descricao=teste anônimo via curl" \
  -F "anonimo=true"
```

- **Esperado:** 201 com o JSON do problema. No banco, esse problema tem
  `autor_cifrado=NULL` e `autor_lookup=NULL` (anônimo, sem vínculo).
- Repita sem `anonimo=true` (ou com `anonimo=false`):
- **Esperado:** 201; no banco, `autor_cifrado` e `autor_lookup` populados,
  vinculando o reporte ao usuário sem expor o `sub` em claro.

### 7. Logout + reproteção

1. Faça logout pelo menu do nav.
2. Tente `http://localhost:3000/conta` novamente.
   - **Esperado:** redirect para `/?login=1&redirectTo=%2Fconta` (a sessão
     foi limpa pelo Supabase SSR).

### 8. Sanity check do middleware reforçado (Item B)

Antes da Fatia 2 fechar, o middleware tinha um regex que tratava qualquer
URL terminada em `.jpg`/`.jpeg`/`.webp`/`.ico` como pública — `/conta/foo.jpg`
bypassava o login wall. Foi corrigido neste task.

1. Deslogado, abra `http://localhost:3000/conta/qualquer-coisa.jpg`
   - **Esperado:** redirect para landing com login modal (mesmo
     comportamento de qualquer outra rota privada).

## Critérios de aprovação

- [ ] Login wall redireciona com `redirectTo` correto em `/mapa`, `/conta`,
      `/conta/feed`.
- [ ] Landing carrega sem modal quando acessada direto.
- [ ] Após login: dashboard `/conta` renderiza com saudação + 3 cards.
- [ ] Composer público cria card com nome real.
- [ ] Composer anônimo cria card com badge "Anônimo" e sem autor.
- [ ] Whitespace puro retorna 422 (não 500).
- [ ] Logout limpa sessão e reativa o login wall.
- [ ] `/conta/foo.jpg` deslogado redireciona pra landing (não bypassa).

## Se algo der errado

- **Dashboard zerado sem motivo aparente:** confira os logs do server Next
  (terminal onde `make dev` roda) — `buscarStats` agora logaria falhas.
- **422 onde deveria criar publicação:** confira o JSON enviado; o front
  precisa fazer `trim()` antes de enviar.
- **500 em vez de 422 no whitespace:** Item E não foi aplicado — confira se
  o validator em `server/app/schemas/publicacao.py` está presente.
- **`/conta/foo.jpg` carrega sem redirect:** Item B regrediu — confira
  `client/src/middleware.ts` `ROTAS_PUBLICAS`.
