from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.domain.entities.health import HealthStatus
from app.usecases.health import HealthUsecase


class DependencyCheckResponse(BaseModel):
    name: str
    ok: bool
    critical: bool
    latency_ms: float
    error: str | None = None


class HealthResponse(BaseModel):
    status: HealthStatus
    checks: list[DependencyCheckResponse] = []


def create_health_router(get_usecase: Callable[..., HealthUsecase]) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["Monitor"])

    @router.get(
        "/live", response_model=HealthResponse, summary="Is the process up? (never touches databases)"
    )
    async def live() -> Any:
        # Liveness must not depend on the database: restarting the API won't fix a database outage.
        return HealthResponse(status=HealthStatus.OK)

    @router.get(
        "/ready",
        response_model=HealthResponse,
        summary="Can it serve requests? 503 when a critical dependency is down",
        responses={503: {"model": HealthResponse}},
    )
    async def ready(response: Response, usecase: Annotated[HealthUsecase, Depends(get_usecase)]) -> Any:
        report = await usecase.readiness()
        if report.status is HealthStatus.DOWN:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return report

    return router
