import uvicorn
from fastapi import FastAPI

from app.config.settings import get_settings
from app.infrastructure.fastapi.server import create_app


def create() -> FastAPI:
    return create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.infrastructure.fastapi.main:create",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
        access_log=False,  # app.access middleware logs requests
    )


if __name__ == "__main__":
    run()
