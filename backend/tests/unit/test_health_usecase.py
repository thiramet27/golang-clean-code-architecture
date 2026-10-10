import asyncio

from app.domain.entities.health import HealthStatus
from app.usecases.health import HealthUsecase


class Probe:
    def __init__(self, name: str, critical: bool, behaviour: str = "ok") -> None:
        self.name, self.critical, self._behaviour = name, critical, behaviour

    async def check(self) -> None:
        if self._behaviour == "fail":
            raise ConnectionRefusedError()
        if self._behaviour == "hang":
            await asyncio.sleep(10)


async def test_all_ok() -> None:
    report = await HealthUsecase([Probe("pg", True), Probe("mongo", False)], 0.5).readiness()
    assert report.status is HealthStatus.OK


async def test_optional_dependency_down_is_degraded() -> None:
    report = await HealthUsecase([Probe("pg", True), Probe("mongo", False, "fail")], 0.5).readiness()
    assert report.status is HealthStatus.DEGRADED
    assert report.checks[1].error == "ConnectionRefusedError"


async def test_hanging_critical_dependency_is_down_within_timeout() -> None:
    started = asyncio.get_running_loop().time()
    report = await HealthUsecase([Probe("pg", True, "hang"), Probe("mongo", False, "hang")], 0.2).readiness()
    assert report.status is HealthStatus.DOWN
    assert asyncio.get_running_loop().time() - started < 0.5  # probes run in parallel
