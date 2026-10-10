import uvicorn
from fastapi import FastAPI

from app.config.settings import get_settings
from app.infrastructure.fastapi.server import create_app


def create() -> FastAPI:
    return create_app()


def run() -> None:
    settings = get_settings()
    reload = settings.env == "development"
    uvicorn.run(
        "app.infrastructure.fastapi.main:create",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=reload,
        # Several processes: CPU work or a stuck request in one worker doesn't stall the others.
        workers=None if reload else settings.workers,
        access_log=False,  # app.access middleware logs requests
        proxy_headers=True,  # real client IP / scheme when running behind nginx
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    run()
