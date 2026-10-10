from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.interface.handlers.fastapi.entities.schemas import MonitorResponse
from app.usecases.monitor import MonitorUsecase


def create_monitor_router(get_usecase: Callable[..., MonitorUsecase]) -> APIRouter:
    router = APIRouter(tags=["Monitor"])

    @router.get("/", response_model=MonitorResponse, summary="Show the name and version of server")
    async def health_check(usecase: Annotated[MonitorUsecase, Depends(get_usecase)]) -> Any:
        return usecase.health_check()

    return router
