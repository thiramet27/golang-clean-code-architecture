# Backend

FastAPI service. Architecture, API and design notes are in the [main README](../README.md).

```bash
uv sync
cp .env.example .env              # or: export GOAPP_DATABASE_URL=sqlite+aiosqlite:///./dev.db
docker compose up -d db mongodb   # skip when using SQLite
make migrate
make dev                          # http://localhost:3000/swagger
make check                        # ruff, mypy --strict, import-linter, pytest
```

Everything in Docker: `docker compose up --build`.
