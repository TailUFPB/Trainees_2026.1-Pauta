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
