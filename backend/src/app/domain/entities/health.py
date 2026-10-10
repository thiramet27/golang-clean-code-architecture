from dataclasses import dataclass, field
from enum import StrEnum


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"  # an optional dependency is down; core features still work
    DOWN = "down"


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    ok: bool
    critical: bool
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True)
class HealthReport:
    status: HealthStatus
    checks: list[DependencyCheck] = field(default_factory=list)
