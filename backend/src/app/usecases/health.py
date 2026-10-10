import asyncio
import time
from typing import Protocol

from app.domain.entities.health import DependencyCheck, HealthReport, HealthStatus


class HealthProbe(Protocol):
    name: str
    critical: bool  # critical = the API can't serve core requests without it

    async def check(self) -> None:
        """Return if the dependency answers; raise otherwise."""
        ...


class HealthUsecase:
    def __init__(self, probes: list[HealthProbe], timeout_s: float) -> None:
        self._probes = probes
        self._timeout = timeout_s

    async def readiness(self) -> HealthReport:
        # All probes run at once, each with its own timeout, so one hanging database
        # can't make the health check itself hang.
        checks = await asyncio.gather(*(self._run(p) for p in self._probes))
        if any(not c.ok and c.critical for c in checks):
            status = HealthStatus.DOWN
        elif any(not c.ok for c in checks):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.OK
        return HealthReport(status=status, checks=list(checks))

    async def _run(self, probe: HealthProbe) -> DependencyCheck:
        started = time.perf_counter()
        error = None
        try:
            await asyncio.wait_for(probe.check(), self._timeout)
        except TimeoutError:
            error = f"no answer within {self._timeout:g}s"
        except Exception as e:  # any failure of the dependency means "not ready"
            error = type(e).__name__
        latency = round((time.perf_counter() - started) * 1000, 1)
        return DependencyCheck(probe.name, error is None, probe.critical, latency, error)
