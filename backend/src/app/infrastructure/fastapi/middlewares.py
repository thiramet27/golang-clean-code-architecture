import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.interface.handlers.fastapi.entities.response import ApiError

ROUTER_CHECK_ERROR = "middlware-001"  # codes kept from the Go version
PARAMS_CHECK_ERROR = "middlware-003"

log = logging.getLogger("app.access")


def add_cors(app: FastAPI, origins: list[str]) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )


def add_access_log(app: FastAPI) -> None:
    @app.middleware("http")
    async def access_log(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        client = request.client.host if request.client else "-"
        log.info(
            "[%s] %s - %s %s %.1fms",
            client,
            response.status_code,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        return response


def add_error_handlers(app: FastAPI) -> None:
    def body(trace_id: str, message: str) -> dict[str, str]:
        return {"trace_id": trace_id, "message": message}

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(body(exc.trace_id, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return JSONResponse(body(PARAMS_CHECK_ERROR, f"{field}: {first['msg']}"), status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(body(ROUTER_CHECK_ERROR, "router not found"), status_code=404)
        return JSONResponse(body(f"http-{exc.status_code}", str(exc.detail)), status_code=exc.status_code)
