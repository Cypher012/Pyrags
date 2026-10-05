.DEFAULT_GOAL := help
INNGEST_NPM_CACHE ?= /tmp/pyrags-inngest-npm-cache-approved

.PHONY: help sync db migrate dev inngest inngest-check

help:
	@printf '%s\n' \
		'make sync           Install dependencies from uv.lock' \
		'make db             Start the local PostgreSQL service' \
		'make migrate        Apply migrations to the development database' \
		'make dev            Start FastAPI in local Inngest mode' \
		'make inngest        Start the Inngest Dev Server in another terminal' \
		'make inngest-check  Inspect the FastAPI Inngest endpoint'

sync:
	uv sync --locked

db:
	docker compose up -d api-db

migrate:
	APP_ENV=development uv run alembic upgrade head

dev:
	APP_ENV=development INNGEST_DEV=1 uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

inngest:
	NPM_CONFIG_CACHE="$(INNGEST_NPM_CACHE)" npx --ignore-scripts=false --allow-scripts=inngest-cli inngest-cli@latest dev --no-discovery -u http://127.0.0.1:8000/api/inngest

inngest-check:
	curl --fail --show-error http://127.0.0.1:8000/api/inngest
