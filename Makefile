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
# Doctor (preflight de pré-requisitos)
# ============================================================================

.PHONY: doctor
doctor: ## Valida pré-requisitos do ambiente (Docker, uv, Node>=20, npm)
	@FAIL=0; \
	if command -v docker >/dev/null 2>&1; then \
		printf "  \033[32m✓\033[0m docker\n"; \
		if docker info >/dev/null 2>&1; then \
			printf "  \033[32m✓\033[0m docker daemon rodando\n"; \
		else \
			printf "  \033[31m✗\033[0m docker daemon não está rodando — inicie o Docker Desktop\n"; \
			FAIL=$$((FAIL+1)); \
		fi; \
	else \
		printf "  \033[31m✗\033[0m docker não encontrado — https://docs.docker.com/get-docker/\n"; \
		FAIL=$$((FAIL+1)); \
	fi; \
	if command -v uv >/dev/null 2>&1; then \
		printf "  \033[32m✓\033[0m uv\n"; \
	else \
		printf "  \033[31m✗\033[0m uv não encontrado — https://docs.astral.sh/uv/getting-started/installation/\n"; \
		FAIL=$$((FAIL+1)); \
	fi; \
	if command -v node >/dev/null 2>&1; then \
		NODE_VER=$$(node --version 2>/dev/null); \
		NODE_MAJOR=$$(printf "%s" "$$NODE_VER" | sed 's/^v//' | cut -d. -f1); \
		if [ "$$NODE_MAJOR" -ge 20 ] 2>/dev/null; then \
			printf "  \033[32m✓\033[0m node %s (>= 20)\n" "$$NODE_VER"; \
		else \
			printf "  \033[31m✗\033[0m node %s — precisa >= 20 (nvm install 20)\n" "$$NODE_VER"; \
			FAIL=$$((FAIL+1)); \
		fi; \
	else \
		printf "  \033[31m✗\033[0m node não encontrado — instale Node >= 20 (nvm install 20)\n"; \
		FAIL=$$((FAIL+1)); \
	fi; \
	if command -v npm >/dev/null 2>&1; then \
		printf "  \033[32m✓\033[0m npm\n"; \
	else \
		printf "  \033[31m✗\033[0m npm não encontrado — vem com Node, reinstale\n"; \
		FAIL=$$((FAIL+1)); \
	fi; \
	if command -v psql >/dev/null 2>&1; then \
		printf "  \033[32m✓\033[0m psql\n"; \
	else \
		printf "  \033[33m⚠\033[0m psql não encontrado — opcional (precisa só pra make db-psql)\n"; \
	fi; \
	if [ -f server/.env ]; then \
		printf "  \033[32m✓\033[0m server/.env\n"; \
		CIFRA=$$(grep -E '^AUTOR_CIFRA_KEY=' server/.env | tail -1 | cut -d= -f2-); \
		if [ -z "$$CIFRA" ]; then \
			printf "  \033[31m✗\033[0m AUTOR_CIFRA_KEY vazia/ausente em server/.env\n"; \
			printf "    Gere com: cd server && uv run python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"; \
			FAIL=$$((FAIL+1)); \
		else \
			printf "  \033[32m✓\033[0m AUTOR_CIFRA_KEY definida\n"; \
		fi; \
		LOOKUP=$$(grep -E '^AUTOR_LOOKUP_KEY=' server/.env | tail -1 | cut -d= -f2-); \
		if [ -z "$$LOOKUP" ]; then \
			printf "  \033[31m✗\033[0m AUTOR_LOOKUP_KEY vazia/ausente em server/.env\n"; \
			FAIL=$$((FAIL+1)); \
		else \
			printf "  \033[32m✓\033[0m AUTOR_LOOKUP_KEY definida\n"; \
		fi; \
		SBURL=$$(grep -E '^SUPABASE_URL=' server/.env | tail -1 | cut -d= -f2-); \
		if [ -z "$$SBURL" ]; then \
			printf "  \033[31m✗\033[0m SUPABASE_URL vazia/ausente em server/.env (necessária pro JWKS do Auth)\n"; \
			FAIL=$$((FAIL+1)); \
		else \
			printf "  \033[32m✓\033[0m SUPABASE_URL definida\n"; \
		fi; \
	else \
		printf "  \033[33m⚠\033[0m server/.env não existe — rode 'make server-env'\n"; \
	fi; \
	if [ -f client/.env.local ]; then \
		printf "  \033[32m✓\033[0m client/.env.local\n"; \
	else \
		printf "  \033[33m⚠\033[0m client/.env.local não existe — rode 'make client-env'\n"; \
	fi; \
	if [ $$FAIL -eq 0 ]; then \
		printf "\n\033[32mtudo certo, bora!\033[0m\n"; \
	else \
		printf "\n\033[31m%s pré-requisito(s) faltando\033[0m\n" "$$FAIL"; \
		exit 1; \
	fi

# ============================================================================
# Guards (helpers internos — prefixados com _ não aparecem no help)
# ============================================================================

.PHONY: _guard-local-db
_guard-local-db:
	@if [ -n "$${DATABASE_URL:-}" ]; then \
		DB_URL="$$DATABASE_URL"; \
		DB_SOURCE="env do shell"; \
	elif [ ! -f server/.env ]; then \
		printf "\033[31m✗ ABORTADO:\033[0m server/.env não existe e DATABASE_URL não está no env. Rode 'make server-env' primeiro.\n"; \
		exit 1; \
	else \
		DB_URL=$$(grep -E '^DATABASE_URL=' server/.env | head -1 | cut -d= -f2- | sed 's/^"//;s/"$$//'); \
		DB_SOURCE="server/.env"; \
	fi; \
	if [ -z "$$DB_URL" ]; then \
		printf "\033[31m✗ ABORTADO:\033[0m DATABASE_URL não encontrada (fonte: %s).\n" "$$DB_SOURCE"; \
		exit 1; \
	fi; \
	HOST=$$(printf "%s" "$$DB_URL" | sed -E 's|^[a-zA-Z0-9+]+://||; s|^[^@/]*@||; s|[:/?].*$$||'); \
	if [ "$$HOST" = "localhost" ] || [ "$$HOST" = "127.0.0.1" ]; then \
		exit 0; \
	fi; \
	if [ "$${PAUTA_ALLOW_REMOTE_DB:-0}" = "1" ]; then \
		printf "\033[33m⚠ PAUTA_ALLOW_REMOTE_DB=1\033[0m — prosseguindo contra host remoto: %s (fonte: %s)\n" "$$HOST" "$$DB_SOURCE"; \
		exit 0; \
	fi; \
	printf "\033[31m✗ ABORTADO:\033[0m DATABASE_URL (%s) aponta pra \"%s\", não pra localhost.\n" "$$DB_SOURCE" "$$HOST"; \
	printf "  Comandos destrutivos só rodam contra o banco local.\n"; \
	printf "  Pra forçar (use com cautela), exporte PAUTA_ALLOW_REMOTE_DB=1.\n"; \
	exit 1

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
db-reset: _guard-local-db ## Apaga volume do banco e sobe do zero (DESTRUTIVO)
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
server-migrate: _guard-local-db ## Aplica todas as migrations do Alembic
	@cd server && uv run alembic upgrade head

.PHONY: server-migrate-down
server-migrate-down: _guard-local-db ## Reverte a última migration
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
server-seed: _guard-local-db ## Popula a tabela políticos com dados de exemplo
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
setup: doctor env server-install client-install ## Setup completo (doctor + envs + deps)
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
