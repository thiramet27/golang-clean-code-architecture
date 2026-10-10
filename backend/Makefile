.PHONY: install dev migrate test lint check up

install:
	uv sync

dev:            ## run API with auto-reload on :3000
	uv run serve

migrate:
	uv run alembic upgrade head

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports

check: lint test

up:             ## Postgres + MongoDB + API in docker
	docker compose up --build
