import asyncio
import time

from tests.conftest import Api


async def test_logins_do_not_freeze_other_requests(api: Api) -> None:
    """bcrypt runs in worker threads; on the event loop, 10 logins would stall /api/v1/ for ~0.5-1 s."""
    await api.register()

    logins = [asyncio.create_task(api.login()) for _ in range(10)]
    await asyncio.sleep(0.01)  # let the logins start hashing

    started = time.perf_counter()
    response = await api.client.get("/api/v1/")
    elapsed = time.perf_counter() - started

    results = await asyncio.gather(*logins)
    assert response.status_code == 200
    assert all(r.status_code == 200 for r in results)
    assert elapsed < 0.15, f"health check took {elapsed:.3f}s while logins were running"


async def test_same_user_logging_in_concurrently(api: Api) -> None:
    """Regression: the session write used to be SELECT-then-INSERT and failed with a unique violation."""
    await api.register()
    results = await asyncio.gather(*(api.login() for _ in range(8)))
    assert [r.status_code for r in results] == [200] * 8
