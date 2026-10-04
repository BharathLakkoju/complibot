.PHONY: bootstrap up down api worker web schemas migrate packs-validate test lint

bootstrap:
	uv sync --all-extras
	cd apps/web && pnpm install
	uv run pre-commit install 2>/dev/null || true

up:
	docker compose up -d
	uv run python scripts/init_localstack.py

down:
	docker compose down

migrate:
	uv run alembic -c apps/api/alembic.ini upgrade head

export PYTHONPATH := packages/complibot/src;.

api:
	uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run python apps/worker/main.py

web:
	pnpm -C apps/web dev

schemas:
	uv run python scripts/codegen_schemas.py

packs-validate:
	uv run python scripts/packs_validate.py

test:
	uv run pytest -q

lint:
	uv run ruff check packages tests scripts
	uv run ruff format --check packages tests scripts
