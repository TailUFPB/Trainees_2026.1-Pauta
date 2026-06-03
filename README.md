# Pauta

Plataforma de transparência política municipal: mapeia problemas de infraestrutura
(geo), acompanha a resolução e recomenda candidatos por afinidade de pautas.

Este repositório contém a **espinha dorsal** do projeto — backend, banco e front base —
onde os módulos de IA do time (LLM de fotos, recomendação, notificações) se conectam.

```
pauta/
├── server/    FastAPI + SQLAlchemy/GeoAlchemy2 + pgvector + Alembic
├── client/    Next.js 16 (App Router) + Supabase + react-leaflet
├── db/        Imagem Postgres com PostGIS + pgvector (dev local)
└── docker-compose.yml
```

## Stack e decisões

- **Banco único**: Postgres com **PostGIS** (geometria dos problemas) + **pgvector**
  (embeddings dos políticos). Em produção é o Postgres do **Supabase**.
- **Auth**: Supabase Auth (JWT). O backend valida o token; o front usa a sessão do SDK.
- **Storage de fotos**: Supabase Storage (com fallback local em dev).
- **Notificações**: o backend só **produz eventos** na tabela `eventos_outbox`. O
  Notification Service (dono a definir: Node/BullMQ ou Python/Celery) consome de lá.

## Subir o ambiente

Caminho rápido (recomendado):

```bash
make setup       # cria .envs, instala deps do server e client
# revise server/.env e client/.env.local
make dev         # sobe banco + migrations + server (:8000) + client (:3000)
```

Veja `make help` para todos os targets disponíveis. Os principais:

- `make db-up` / `make db-down` / `make db-reset` — banco local (Docker)
- `make server-dev` / `make server-test` / `make server-migrate` — backend
- `make client-dev` / `make client-build` / `make client-lint` — frontend
- `make check-all` / `make ci` — lint + typecheck (+ testes/build no `ci`)

### Passo-a-passo manual (alternativa)

#### 1. Banco (Docker)

```bash
docker compose up -d --build      # Postgres + PostGIS + pgvector na porta 5432
```

#### 2. Backend

```bash
cd server
cp .env.example .env              # ajuste SUPABASE_* para usar Auth/Storage reais
uv sync
uv run alembic upgrade head       # cria extensões + tabelas
uv run uvicorn app.main:app --reload --port 8000
```

Docs interativas (Swagger): http://localhost:8000/docs

```bash
uv run pytest                     # roda os testes (precisa do banco no ar)
```

#### 3. Front

```bash
cd client
cp .env.example .env.local        # preencha NEXT_PUBLIC_SUPABASE_* e a URL da API
npm install
npm run dev                       # http://localhost:3000
```

## Comandos do Makefile

```bash
make                  # mostra todos os targets (mesmo que make help)
make setup            # 1ª vez: cria .envs, instala deps do server e client
make dev              # sobe db + migrations + server (:8000) + client (:3000)
                      # Ctrl+C mata tudo
```

Dia a dia:

```bash
make db-up            # só o banco (docker)
make db-psql          # abre psql conectado no banco
make server-dev       # só o backend
make client-dev       # só o front
make server-test      # pytest
make server-migrate                              # aplica migrations
make server-migrate-create MSG="adiciona x"      # cria nova migration
make client-lint      # ESLint
make check-all        # lint + typecheck (server + client)
```

Se algo travar porta:

```bash
make dev-stop         # mata processos órfãos em :8000 e :3000
make clean            # limpa caches (.next, __pycache__, mypy, ruff)
```

`make help` sempre te lembra do resto.

## O que está pronto (fatia vertical) vs. contrato+stub

| Área | Estado |
|------|--------|
| Reportar problema + mapa | **End-to-end** (front + back + geo + evento) |
| Recomendação de candidatos | Contrato + query pgvector prontos; aguarda embeddings |
| Notificações | Produção de eventos no outbox pronta; consumidor é de outro dono |
| LLM de fotos | Interface/stub pronta; classificação real é de outro dono |

## Pontos de integração para o time (seams)

Tudo o que é IA mora em `server/app/services/` com **assinatura fixa** — preencha o corpo
sem tocar em rotas, banco ou contratos:

- **LLM de fotos** — `services/visao.py::classificar(imagem: bytes) -> ClassificacaoFoto`.
  Hoje é um stub determinístico; troque pela chamada ao MLLM (ex.: Gemini 2.5 Flash).
- **Recomendação** — `services/recomendacao.py::gerar_embedding(texto) -> list[float]`
  (stub) e `top_politicos_por_similaridade(...)` (query de cosseno pronta). A dimensão
  do embedding é `EMBEDDING_DIM` (`.env`, default 768) e **deve bater** com o modelo do
  pipeline offline que popula `politicos.embedding`.
- **Notificações** — `services/eventos.py`. O backend grava em `eventos_outbox`
  (`tipo`, `payload`, `prioridade`, `processado_em IS NULL` = pendente). O consumidor lê
  os pendentes, dispara push/email e marca como processados.

## Coordenação pendente

- **`EMBEDDING_DIM`** precisa ser combinado com o colega da recomendação.
- **Random Forest** (citado na documentação inicial) foi **descartado** pelo time em
  favor de embeddings + similaridade de cosseno + k-means. Alinhar a doc-mãe.
- **Consumidor do outbox** (Node vs Python) é decisão de time.
