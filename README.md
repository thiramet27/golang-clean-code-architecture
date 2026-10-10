## Python version (FastAPI) + frontend

This fork adds a Python rewrite of the Go template below, plus a small React app that uses it.

| Folder | What |
|---|---|
| [`backend-python/`](backend-python) | FastAPI + SQLAlchemy 2 + Alembic, same layers and API as the Go code. Structure, design notes and the list of fixes are in its [README](backend-python/README.md). |
| [`frontend/`](frontend) | React + TypeScript client: register / login / profile, and a data browser whose table columns come from the API's `data_schema`. |

```bash
cd backend-python && uv sync && cp .env.example .env
GOAPP_DATABASE_URL=sqlite+aiosqlite:///./dev.db uv run alembic upgrade head
GOAPP_DATABASE_URL=sqlite+aiosqlite:///./dev.db uv run serve      # http://localhost:3000/swagger

cd frontend && pnpm install && pnpm dev                              # http://localhost:5173
```

The original Go template is unchanged below and in `src/`.

---

## Golang Clean Code Architecture Template

Go (Golang) Clean Architecture based on Reading Uncle Bob's Clean Architecture. This code using GoFiber, GORM and User registerm authentication feature.

## Installation
1. Replace "github.com/max38/golang-clean-code-architecture" with "your module name"
2. Copy or Change "env.template" file name to ".env" or ".env.dev"
3. Check on code for loading config in these files
```
src/infrastructure/database/postgres/migration/main.go
src/infrastructure/gofiber/main.go
```

4. Run Postgresql
5. Migrate RDBMS
6. Start web project


### run postgresql on docker
```bash
docker run -p 5432:5432 --name postgres-golang-first-api -e POSTGRES_PASSWORD=golang-first-api -d postgres:15
```
or docker compose
```bash
docker-compose up
```

### Migrate RDBMS
```bash
go run src/infrastructure/database/postgres/migration/main.go
```

### start web project (Production)

```bash
go run src/infrastructure/gofiber/main.go
```


# Template for every projdct
## Project Structure
```
src
 |-config
 |-domain
    |-entities
    |-models
    |-repositories
 |-infrastructure
    |-aws_lambda
    |-database
    |-gofiber
 |-interface
    |-handlers
       |-gofiber
    |-repositories
       |-postgres
 |-shared
 |-usecases
```

## Install lib

### REST API Lib
```bash
go get github.com/gofiber/fiber/v2
```

### Generate Swagger Document
1. Install follow this https://github.com/gofiber/swagger
2. Go to ChatGPT and prompt with
```
Please generate Declarative Comments Format for Swagger Doc follow this gofiber code.
"""<Handler Code>"""
```

3. update Declarative Comments from ChatGPT to Handler

4. Generate swagger.json
```bash
swag init -g src/infrastructure/gofiber/main.go -o src/infrastructure/gofiber/docs/
```

5. Go to localhost:3000/swagger/


### Configuration Lib
```bash
go get github.com/knadh/koanf/v2
go get github.com/knadh/koanf/providers/file
go get github.com/knadh/koanf/providers/env
go get github.com/knadh/koanf/parsers/dotenv
```

### GORM
```bash
go get -u gorm.io/gorm
go get -u gorm.io/driver/postgresql
```

### MongoDB
if use mongodb
```bash
go get go.mongodb.org/mongo-driver
go get go.mongodb.org/mongo-driver/mongo
```


## For Development

### Install Gofiber cli
follow this https://github.com/gofiber/cli

### start web project (Development)

```bash
fiber dev -t ./src/infrastructure/gofiber/main.go
```

### Add More Model
1. Define in src/domain/models/xxxx.go
2. Add Model at src/config/crudModels.go
