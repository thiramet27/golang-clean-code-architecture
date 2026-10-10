FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV GOAPP_HOST=0.0.0.0 GOAPP_ENV=production
EXPOSE 3000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync serve"]
