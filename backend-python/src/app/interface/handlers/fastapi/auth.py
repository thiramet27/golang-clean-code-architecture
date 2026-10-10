from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.entities.user import User
from app.domain.errors import DomainError
from app.interface.handlers.fastapi.entities.response import ApiError
from app.usecases.user.user_usecase import UserUsecase

JWT_AUTH_ERROR = "middlware-002"  # same code as the Go version

bearer = HTTPBearer(auto_error=False, description="Access token from /users/login")


@dataclass(frozen=True)
class AuthContext:
    user: User
    permission: str | None


def create_jwt_auth(
    get_user_usecase: Callable[..., UserUsecase | Awaitable[UserUsecase]],
) -> Callable[..., Awaitable[AuthContext]]:
    """Go: middlewares.JwtAuth(). Returned as a FastAPI dependency instead of a middleware."""

    async def jwt_auth(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
        usecase: Annotated[UserUsecase, Depends(get_user_usecase, scope="function")],
    ) -> AuthContext:
        if credentials is None:
            raise ApiError(401, JWT_AUTH_ERROR, "missing bearer token")
        try:
            user, permission = await usecase.authenticate(credentials.credentials)
        except DomainError as e:
            raise ApiError(401, JWT_AUTH_ERROR, e.message) from e
        return AuthContext(user=user, permission=permission)

    return jwt_auth
