from pydantic import BaseModel

from app.domain.errors import (
    DomainError,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class ErrorResponse(BaseModel):
    """Same error body as the Go version: {"trace_id": "users-001", "message": "..."}"""

    trace_id: str
    message: str


class ApiError(Exception):
    def __init__(self, status_code: int, trace_id: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id
        self.message = message


DEFAULT_STATUS: dict[type[DomainError], int] = {
    ValidationError: 400,
    EmailAlreadyUsedError: 409,
    InvalidCredentialsError: 400,
    InvalidTokenError: 400,
    NotFoundError: 404,
    PermissionDeniedError: 403,
}


def to_api_error(
    error: DomainError, trace_id: str, overrides: dict[type[DomainError], int] | None = None
) -> ApiError:
    statuses = {**DEFAULT_STATUS, **(overrides or {})}
    # Walk the class hierarchy so TokenExpiredError uses the InvalidTokenError status, etc.
    status = next((statuses[cls] for cls in type(error).__mro__ if cls in statuses), 400)
    return ApiError(status, trace_id, error.message)
