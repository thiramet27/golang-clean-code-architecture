import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import Settings, get_settings
from app.infrastructure.fastapi.container import Container
from app.infrastructure.fastapi.middlewares import add_access_log, add_cors, add_error_handlers
from app.interface.handlers.fastapi.auth import create_jwt_auth
from app.interface.handlers.fastapi.modules.crud import create_crud_router
from app.interface.handlers.fastapi.modules.monitor import create_monitor_router
from app.interface.handlers.fastapi.modules.user import create_user_router

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = container or Container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await container.close()  # graceful shutdown: close DB pools

    app = FastAPI(
        title=settings.name,
        version=settings.version,
        description="Python (FastAPI) port of golang-clean-code-architecture",
        docs_url="/swagger",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.container = container

    add_cors(app, settings.cors_origins)
    add_access_log(app)
    add_error_handlers(app)

    jwt_auth = create_jwt_auth(container.get_user_usecase)
    app.include_router(create_monitor_router(container.get_monitor_usecase), prefix=API_PREFIX)
    app.include_router(create_user_router(container.get_user_usecase, jwt_auth), prefix=API_PREFIX)
    app.include_router(create_crud_router(container.get_crud_usecase, jwt_auth), prefix=API_PREFIX)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return app
