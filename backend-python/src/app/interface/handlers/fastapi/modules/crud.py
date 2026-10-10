from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.domain.entities.crud import PageRequest
from app.domain.errors import DomainError, EntityModelNotFoundError, NotFoundError, PermissionDeniedError
from app.interface.handlers.fastapi.auth import AuthContext
from app.interface.handlers.fastapi.entities.response import ErrorResponse, to_api_error
from app.interface.handlers.fastapi.entities.schemas import DataListResponseModel, DataResponseModel
from app.usecases.crud.crud_usecase import CrudUsecase

DATA_ERROR = "data-001"
RESERVED_QUERY = {"_page", "_pageSize"}

ERRORS: dict[int | str, dict[str, Any]] = {code: {"model": ErrorResponse} for code in (400, 401, 403, 404)}


def _error(e: DomainError) -> Exception:
    return to_api_error(
        e, DATA_ERROR, {EntityModelNotFoundError: 404, NotFoundError: 404, PermissionDeniedError: 403}
    )


def create_crud_router(
    get_usecase: Callable[..., Any],
    jwt_auth: Callable[..., Awaitable[AuthContext]],
) -> APIRouter:
    router = APIRouter(prefix="/data", tags=["Data"], responses=ERRORS)
    Usecase = Annotated[CrudUsecase, Depends(get_usecase, scope="function")]
    Auth = Annotated[AuthContext, Depends(jwt_auth, scope="function")]

    @router.get("/{entity_model_slug}/describe", summary="Avro-style schema of a model")
    async def describe(
        entity_model_slug: str,
        auth: Auth,
        usecase: Usecase,
    ) -> dict[str, Any]:
        try:
            return usecase.describe(auth.permission, entity_model_slug.strip())
        except DomainError as e:
            raise _error(e) from e

    @router.get(
        "/{entity_model_slug}/",
        response_model=DataListResponseModel,
        summary="List records. Any other query param is an exact-match filter, e.g. ?email=a@b.com",
    )
    async def retrieve_list(
        entity_model_slug: str,
        request: Request,
        auth: Auth,
        usecase: Usecase,
        page: Annotated[int, Query(alias="_page")] = 1,
        page_size: Annotated[int, Query(alias="_pageSize")] = 10,
    ) -> Any:
        # The Go handler parsed filters but then passed nil; here they are applied (whitelisted by column).
        filters = {k: v for k, v in request.query_params.items() if k not in RESERVED_QUERY}
        try:
            return await usecase.retrieve_list(
                auth.permission, entity_model_slug.strip(), PageRequest(page, page_size), filters
            )
        except DomainError as e:
            raise _error(e) from e

    @router.get("/{entity_model_slug}/{record_id}", response_model=DataResponseModel)
    async def retrieve(
        entity_model_slug: str,
        record_id: str,
        auth: Auth,
        usecase: Usecase,
    ) -> Any:
        try:
            return await usecase.retrieve(auth.permission, entity_model_slug.strip(), record_id)
        except DomainError as e:
            raise _error(e) from e

    return router
