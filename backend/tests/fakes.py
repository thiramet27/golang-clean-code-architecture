from dataclasses import replace
from datetime import UTC, datetime

from app.domain.entities.user import User, UserCredentials, UserSession
from app.domain.errors import EmailAlreadyUsedError
from app.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[int, UserCredentials] = {}
        self.sessions: dict[int, UserSession] = {}
        self.permissions: dict[int, str] = {}

    async def get_by_email(self, email: str) -> UserCredentials | None:
        return next((c for c in self.users.values() if c.user.email == email), None)

    async def get_by_id(self, user_id: int) -> User | None:
        c = self.users.get(user_id)
        return c.user if c else None

    async def insert(self, email: str, password_hash: str, first_name: str, last_name: str) -> User:
        if await self.get_by_email(email):
            raise EmailAlreadyUsedError()
        now = datetime.now(UTC)
        user = User(len(self.users) + 1, email, first_name, last_name, now, now)
        self.users[user.id] = UserCredentials(user, password_hash)
        return user

    async def save_session(self, session: UserSession) -> None:
        self.sessions[session.user_id] = replace(session)

    async def find_session(self, user_id: int) -> UserSession | None:
        return self.sessions.get(user_id)

    async def delete_session(self, user_id: int) -> None:
        self.sessions.pop(user_id, None)

    async def get_permission(self, user_id: int) -> str | None:
        return self.permissions.get(user_id)


class FakeHasher:
    """Fast and readable; bcrypt itself is covered by the API tests."""

    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    async def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class Clock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now
