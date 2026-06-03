.DEFAULT_GOAL := help

# ============================================================================
# Variáveis (sobrescreva via `make VAR=valor target` ou via env)
# ============================================================================

DB_SERVICE       ?= db
DB_USER          ?= pauta
DB_NAME          ?= pauta
SERVER_PORT      ?= 8000
CLIENT_PORT      ?= 3000
DOCKER_COMPOSE   ?= docker compose

# ============================================================================
# Ajuda
# ============================================================================

.PHONY: help
help: ## Lista todos os targets disponíveis
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ============================================================================
# Banco (Docker Compose: Postgres + PostGIS + pgvector)
# ============================================================================

.PHONY: db-up
db-up: ## Sobe o banco (Postgres) e espera ficar saudável
	@$(DOCKER_COMPOSE) up -d --build --wait $(DB_SERVICE)
	@echo "Banco pronto em localhost:5432 (user=$(DB_USER), db=$(DB_NAME))"

.PHONY: db-down
db-down: ## Para o banco (preserva o volume)
	@$(DOCKER_COMPOSE) stop $(DB_SERVICE)

.PHONY: db-reset
db-reset: ## Apaga volume do banco e sobe do zero (DESTRUTIVO)
	@$(DOCKER_COMPOSE) down -v
	@$(MAKE) db-up
	@echo "Banco resetado. Rode 'make server-migrate' para recriar o schema."

.PHONY: db-logs
db-logs: ## Tail dos logs do banco
	@$(DOCKER_COMPOSE) logs -f $(DB_SERVICE)

.PHONY: db-psql
db-psql: ## Abre psql no banco
	@$(DOCKER_COMPOSE) exec $(DB_SERVICE) psql -U $(DB_USER) -d $(DB_NAME)

# ============================================================================
# Server (FastAPI + uv + Alembic)
# ============================================================================

.PHONY: server-install
server-install: ## Instala dependências do backend (uv sync com dev group)
	@cd server && uv sync --group dev

.PHONY: server-env
server-env: ## Cria server/.env a partir do .env.example (idempotente)
	@if [ ! -f server/.env ]; then \
		cp server/.env.example server/.env; \
		echo "Criado server/.env (revise as variáveis)."; \
	else \
		echo "server/.env já existe."; \
	fi

.PHONY: server-dev
server-dev: ## Sobe o server FastAPI em modo dev (porta $(SERVER_PORT))
	@cd server && uv run uvicorn app.main:app --reload --port $(SERVER_PORT)

.PHONY: server-test
server-test: ## Roda os testes do backend (precisa do banco no ar)
	@cd server && uv run pytest

.PHONY: server-lint
server-lint: ## Lint do backend (ruff check)
	@cd server && uv run ruff check .

.PHONY: server-format
server-format: ## Formata o backend (ruff format)
	@cd server && uv run ruff format .

.PHONY: server-typecheck
server-typecheck: ## Typecheck do backend (mypy)
	@cd server && uv run mypy app/

.PHONY: server-migrate
server-migrate: ## Aplica todas as migrations do Alembic
	@cd server && uv run alembic upgrade head

.PHONY: server-migrate-down
server-migrate-down: ## Reverte a última migration
	@cd server && uv run alembic downgrade -1

.PHONY: server-migrate-status
server-migrate-status: ## Mostra estado atual e histórico de migrations
	@cd server && uv run alembic current
	@cd server && uv run alembic history

.PHONY: server-migrate-create
server-migrate-create: ## Cria nova migration (uso: make server-migrate-create MSG="descrição")
	@if [ -z "$(MSG)" ]; then echo "Uso: make server-migrate-create MSG=\"descrição\""; exit 1; fi
	@cd server && uv run alembic revision --autogenerate -m "$(MSG)"

.PHONY: server-seed
server-seed: ## Popula a tabela políticos com dados de exemplo
	@cd server && uv run python -m app.cli.seed_politicos

# ============================================================================
# Client (Next.js + npm)
# ============================================================================

.PHONY: client-install
client-install: ## Instala dependências do frontend (npm install)
	@cd client && npm install

.PHONY: client-env
client-env: ## Cria client/.env.local a partir do .env.example (idempotente)
	@if [ ! -f client/.env.local ]; then \
		cp client/.env.example client/.env.local; \
		echo "Criado client/.env.local (preencha NEXT_PUBLIC_SUPABASE_* e a URL da API)."; \
	else \
		echo "client/.env.local já existe."; \
	fi

.PHONY: client-dev
client-dev: ## Sobe o client Next.js em modo dev (porta $(CLIENT_PORT))
	@cd client && PORT=$(CLIENT_PORT) npm run dev

.PHONY: client-build
client-build: ## Build de produção do client
	@cd client && npm run build

.PHONY: client-start
client-start: ## Roda o build de produção (precisa de 'make client-build' antes)
	@cd client && PORT=$(CLIENT_PORT) npm run start

.PHONY: client-lint
client-lint: ## Lint do client (ESLint)
	@cd client && npm run lint

.PHONY: client-clean
client-clean: ## Limpa cache do Next (.next) — útil após mudar envs
	@rm -rf client/.next
	@echo "client/.next removido."

# ============================================================================
# Orquestração (executar tudo de uma vez)
# ============================================================================

.PHONY: env
env: server-env client-env ## Cria os .env locais para server e client (idempotente)

.PHONY: setup
setup: env server-install client-install ## Setup completo (envs + deps do server e client)
	@echo ""
	@echo "Setup concluído. Próximos passos:"
	@echo "  1. Revise server/.env e client/.env.local"
	@echo "  2. Rode 'make dev' para subir tudo"

.PHONY: lint-all
lint-all: server-lint client-lint ## Lint em server + client

.PHONY: format-all
format-all: server-format ## Formata server (client formata via lint --fix se quiser)

.PHONY: check-all
check-all: server-lint server-typecheck client-lint ## Lint + typecheck em tudo

.PHONY: dev
dev: db-up server-migrate ## Sobe tudo: db (com migrations) + server + client em paralelo
	@echo ""
	@echo "Subindo server (:$(SERVER_PORT)) e client (:$(CLIENT_PORT))..."
	@echo "Logs misturados. Ctrl+C para parar tudo."
	@echo ""
	@trap 'kill 0' EXIT; \
		($(MAKE) server-dev) & \
		($(MAKE) client-dev) & \
		wait

.PHONY: dev-stop
dev-stop: ## Mata processos órfãos em :$(SERVER_PORT) e :$(CLIENT_PORT)
	@lsof -ti:$(SERVER_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null; true
	@lsof -ti:$(CLIENT_PORT) 2>/dev/null | xargs -r kill -9 2>/dev/null; true
	@echo "Portas $(SERVER_PORT) e $(CLIENT_PORT) liberadas."

.PHONY: clean
clean: client-clean ## Limpa caches (Next, pycache, mypy_cache, ruff_cache)
	@find server -type d -name __pycache__ -prune -exec rm -rf {} +
	@rm -rf server/.mypy_cache server/.ruff_cache server/.pytest_cache
	@echo "Caches removidos."

.PHONY: ci
ci: check-all server-test client-build ## Roda o que CI rodaria: lint + typecheck + test + build
