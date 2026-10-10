from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.user import NewUser
from app.domain.errors import (
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    ValidationError,
)
from app.infrastructure.security.jwt_tokens import JwtTokenService
from app.usecases.user.user_usecase import UserUsecase, token_digest
from tests.fakes import Clock, FakeHasher, InMemoryUserRepository

START = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> Clock:
    return Clock(START)


@pytest.fixture
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def usecase(repo: InMemoryUserRepository, clock: Clock) -> UserUsecase:
    tokens = JwtTokenService(
        "unit-test-secret-0123456789abcdef", "test", timedelta(hours=1), timedelta(days=2), now=clock
    )
    return UserUsecase(repo, FakeHasher(), tokens)


async def registered(usecase: UserUsecase, email: str = "a@example.com") -> None:
    await usecase.register(NewUser(email, "password123", "A", "B"))


async def test_register_stores_hash_and_normalises_email(
    usecase: UserUsecase, repo: InMemoryUserRepository
) -> None:
    user = await usecase.register(NewUser("Somchai@Example.com", "password123", "Somchai", "J"))
    assert user.email == "somchai@example.com"
    assert repo.users[user.id].password_hash == "hashed:password123"


async def test_register_rejects_short_password(usecase: UserUsecase) -> None:
    with pytest.raises(ValidationError):
        await usecase.register(NewUser("a@example.com", "short", "", ""))


async def test_register_rejects_duplicate_email(usecase: UserUsecase) -> None:
    await registered(usecase)
    with pytest.raises(EmailAlreadyUsedError):
        await registered(usecase, "A@example.com")


async def test_login_gives_same_error_for_unknown_email_and_wrong_password(usecase: UserUsecase) -> None:
    await registered(usecase)
    with pytest.raises(InvalidCredentialsError) as wrong_password:
        await usecase.login("a@example.com", "nope-nope")
    with pytest.raises(InvalidCredentialsError) as unknown_email:
        await usecase.login("ghost@example.com", "password123")
    assert wrong_password.value.message == unknown_email.value.message


async def test_login_stores_token_digests_not_raw_tokens(
    usecase: UserUsecase, repo: InMemoryUserRepository
) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    session = repo.sessions[result.user.id]
    assert session.access_digest == token_digest(result.token.access)
    assert result.token.access not in (session.access_digest, session.refresh_digest)


async def test_authenticate_with_access_token(usecase: UserUsecase, repo: InMemoryUserRepository) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    repo.permissions[result.user.id] = "admin"
    user, permission = await usecase.authenticate(result.token.access)
    assert (user.email, permission) == ("a@example.com", "admin")


async def test_tokens_cannot_be_used_for_the_other_purpose(usecase: UserUsecase) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    with pytest.raises(InvalidTokenError):
        await usecase.authenticate(result.token.refresh)
    with pytest.raises(InvalidTokenError):
        await usecase.refresh_token(result.token.access)


async def test_refresh_rotates_tokens_and_old_refresh_stops_working(
    usecase: UserUsecase, clock: Clock
) -> None:
    await registered(usecase)
    first = await usecase.login("a@example.com", "password123")
    clock.now += timedelta(minutes=5)

    second = await usecase.refresh_token(first.token.refresh)
    assert second.token.access != first.token.access
    assert second.token.refresh != first.token.refresh
    with pytest.raises(InvalidTokenError):
        await usecase.refresh_token(first.token.refresh)
    with pytest.raises(InvalidTokenError):
        await usecase.authenticate(first.token.access)


async def test_refresh_keeps_original_expiry_so_sessions_cannot_live_forever(
    usecase: UserUsecase, clock: Clock
) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    clock.now += timedelta(days=1)
    result = await usecase.refresh_token(result.token.refresh)
    clock.now += timedelta(days=1, seconds=1)  # 2 days after login
    with pytest.raises(TokenExpiredError):
        await usecase.refresh_token(result.token.refresh)


async def test_logout_revokes_access_token(usecase: UserUsecase) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    await usecase.logout(result.token.refresh)
    with pytest.raises(InvalidTokenError):
        await usecase.authenticate(result.token.access)


async def test_login_again_revokes_previous_session(usecase: UserUsecase) -> None:
    await registered(usecase)
    old = await usecase.login("a@example.com", "password123")
    await usecase.login("a@example.com", "password123")
    with pytest.raises(InvalidTokenError):
        await usecase.authenticate(old.token.access)


async def test_expired_access_token(usecase: UserUsecase, clock: Clock) -> None:
    await registered(usecase)
    result = await usecase.login("a@example.com", "password123")
    clock.now += timedelta(hours=1, seconds=1)
    with pytest.raises(TokenExpiredError):
        await usecase.authenticate(result.token.access)
