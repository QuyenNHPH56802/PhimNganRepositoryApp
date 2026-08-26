# Translator — convenience targets
# Works on macOS/Linux. On Windows use `scripts/up.ps1`.

PROJECT := translator
COMPOSE  := docker compose -f infra/docker/docker-compose.yml

.PHONY: help up down logs restart build buildx-up psql wait temporal-ui test lint typecheck \
        smoke real-stack helm-lint helm-template docusaurus

help:
	@echo "Translator commands:"
	@echo "  make up            start API + Worker + Web + Postgres + Temporal"
	@echo "  make down          stop the stack (volumes persist)"
	@echo "  make logs          tail logs from all services"
	@echo "  make psql          open psql into the dev database"
	@echo "  make temporal-ui   open Temporal UI in browser"
	@echo "  make test          run unit tests"
	@echo "  make typecheck     tsc on SDK + mypy on Python packages"
	@echo "  make smoke         call /healthz and /readyz"
	@echo "  make helm-template render Helm chart v1.0"

up:
	$(COMPOSE) up -d --build
	@echo "Waiting for services …"
	@$(MAKE) --no-print-directory wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

restart:
	$(COMPOSE) restart api worker web

build:
	$(COMPOSE) build --pull

psql:
	$(COMPOSE) exec db psql -U postgres -d translator

temporal-ui:
	@echo "Temporal UI: http://localhost:8233"

wait:
	@echo "Waiting for Postgres …"
	@$(COMPOSE) exec -T db pg_isready -U postgres -d translator
	@echo "Waiting for Temporal …"
	@for i in $$(seq 1 30); do \
	    if $(COMPOSE) exec -T temporal tctl --address temporal:7233 cluster health 2>/dev/null | grep -q SERVING; then \
	        echo "Temporal is up"; exit 0; \
	    fi; \
	    sleep 2; \
	done
	@echo "Waiting for API …"
	@for i in $$(seq 1 30); do \
	    if curl -sf http://localhost:8000/healthz >/dev/null; then \
	        echo "API is up"; exit 0; \
	    fi; \
	    sleep 2; \
	done

smoke:
	curl -s http://localhost:8000/healthz | tee /dev/stderr | jq -e .status >/dev/null
	curl -s http://localhost:8000/readyz | jq -e .status >/dev/null

test:
	pytest -q

typecheck:
	cd apps/web/sdk && npm run typecheck
	mypy apps

helm-template:
	helm template translator infra/helm/translator