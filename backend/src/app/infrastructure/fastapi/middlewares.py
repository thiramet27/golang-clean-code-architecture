import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure, ExecutionTimeout, ServerSelectionTimeoutError
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infrastructure.logging import request_id_var
from app.interface.handlers.fastapi.entities.response import ApiError

ROUTER_CHECK_ERROR = "middlware-001"  # codes kept from the Go version
PARAMS_CHECK_ERROR = "middlware-003"
DB_UNAVAILABLE = "db-unavailable"
INTERNAL_ERROR = "internal-error"
REQUEST_ID_HEADER = "X-Request-ID"
VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

log = logging.getLogger("app.access")
error_log = logging.getLogger("app.error")

# Errors that mean "a database is down, slow or out of connections", not "the code is wrong".
UNAVAILABLE_ERRORS = (
    OperationalError,
    InterfaceError,
    PoolTimeoutError,
    ConnectionFailure,  # includes Mongo network errors and timeouts
    ServerSelectionTimeoutError,
    ExecutionTimeout,
    ConnectionError,
    TimeoutError,
)


def is_database_unavailable(exc: BaseException) -> bool:
    if isinstance(exc, UNAVAILABLE_ERRORS):
        return True
    # asyncpg reports a cancelled statement (statement_timeout) as a generic DBAPIError
    return isinstance(exc, DBAPIError) and "statement timeout" in str(exc.orig)


def add_cors(app: FastAPI, origins: list[str]) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )


def add_request_context(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            client = request.client.host if request.client else "-"
            log.info("[%s] %s - %s %s %.1fms", client, status, request.method, request.url.path, elapsed_ms)
            request_id_var.reset(token)


def add_error_handlers(app: FastAPI) -> None:
    def respond(request: Request, status: int, trace_id: str, message: str) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            {"trace_id": trace_id, "message": message, "request_id": request_id},
            status_code=status,
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return respond(request, exc.status_code, exc.trace_id, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return respond(request, 400, PARAMS_CHECK_ERROR, f"{field}: {first['msg']}")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return respond(request, 404, ROUTER_CHECK_ERROR, "router not found")
        return respond(request, exc.status_code, f"http-{exc.status_code}", str(exc.detail))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        if is_database_unavailable(exc):
            error_log.warning("database unavailable: %s: %s", type(exc).__name__, exc)
            return respond(request, 503, DB_UNAVAILABLE, "database is unavailable, please try again shortly")
        # Full details stay in the server log; the client only gets the request id to report.
        error_log.exception("unhandled error on %s %s", request.method, request.url.path)
        return respond(request, 500, INTERNAL_ERROR, "unexpected error")
