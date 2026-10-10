from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from app.domain.entities.user import NewUser
from app.domain.errors import DomainError
from app.interface.handlers.fastapi.auth import AuthContext
from app.interface.handlers.fastapi.entities.response import ErrorResponse, to_api_error
from app.interface.handlers.fastapi.entities.schemas import (
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.usecases.user.user_usecase import UserUsecase

REGISTER_USER_ERROR = "users-001"
LOGIN_USER_ERROR = "users-002"
REFRESH_TOKEN_ERROR = "users-003"
LOGOUT_USER_ERROR = "users-004"

ERRORS: dict[int | str, dict[str, Any]] = {400: {"model": ErrorResponse}}


def create_user_router(
    get_usecase: Callable[..., Any],
    jwt_auth: Callable[..., Awaitable[AuthContext]],
) -> APIRouter:
    router = APIRouter(prefix="/users", tags=["User"], responses=ERRORS)
    Usecase = Annotated[UserUsecase, Depends(get_usecase, scope="function")]
    Auth = Annotated[AuthContext, Depends(jwt_auth, scope="function")]

    @router.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        response_model=UserResponse,
        responses={409: {"model": ErrorResponse}},
    )
    async def register_user(body: UserRegisterRequest, usecase: Usecase) -> Any:
        try:
            return await usecase.register(NewUser(**body.model_dump()))
        except DomainError as e:
            raise to_api_error(e, REGISTER_USER_ERROR) from e

    @router.post("/login", response_model=UserLoginResponse)
    async def user_login(body: UserLoginRequest, usecase: Usecase) -> Any:
        try:
            return await usecase.login(body.email, body.password)
        except DomainError as e:
            raise to_api_error(e, LOGIN_USER_ERROR) from e

    @router.post("/logout", response_model=None)
    async def user_logout(body: UserRefreshTokenRequest, usecase: Usecase) -> None:
        try:
            await usecase.logout(body.refresh_token)
        except DomainError as e:
            raise to_api_error(e, LOGOUT_USER_ERROR) from e

    @router.post("/refresh-token", response_model=UserLoginResponse)
    async def refresh_token(body: UserRefreshTokenRequest, usecase: Usecase) -> Any:
        try:
            return await usecase.refresh_token(body.refresh_token)
        except DomainError as e:
            raise to_api_error(e, REFRESH_TOKEN_ERROR) from e

    # Go registers POST /profile while its swagger says GET; both work here.
    @router.api_route(
        "/profile",
        methods=["GET", "POST"],
        response_model=UserResponse,
        responses={401: {"model": ErrorResponse}},
    )
    async def get_user_profile(auth: Auth) -> Any:
        return auth.user

    return router
