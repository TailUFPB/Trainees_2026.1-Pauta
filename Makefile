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
