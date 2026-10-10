import errno
import socket

import pytest
from pymongo.errors import ServerSelectionTimeoutError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.infrastructure.fastapi.middlewares import is_database_unavailable


def wrapped(inner: BaseException) -> Exception:
    try:
        try:
            raise inner
        except BaseException as e:
            raise RuntimeError("driver wrapper") from e
    except RuntimeError as outer:
        return outer


@pytest.mark.parametrize(
    "exc",
    [
        socket.gaierror(
            -3, "Temporary failure in name resolution"
        ),  # seen in production: db container stopped
        ConnectionRefusedError(errno.ECONNREFUSED, "refused"),
        OSError(errno.EHOSTUNREACH, "no route to host"),
        TimeoutError(),
        PoolTimeoutError("QueuePool limit reached"),
        OperationalError("SELECT 1", None, Exception("server closed the connection")),
        ServerSelectionTimeoutError("no servers"),
        wrapped(socket.gaierror(-3, "dns")),
    ],
    ids=lambda e: type(e).__name__,
)
def test_outages_are_recognised(exc: BaseException) -> None:
    assert is_database_unavailable(exc)


@pytest.mark.parametrize(
    "exc",
    [ValueError("bug"), KeyError("x"), FileNotFoundError(errno.ENOENT, "nope"), wrapped(ZeroDivisionError())],
)
def test_programming_errors_are_not_hidden_as_503(exc: BaseException) -> None:
    assert not is_database_unavailable(exc)
