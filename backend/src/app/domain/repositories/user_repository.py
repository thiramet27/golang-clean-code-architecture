from abc import ABC, abstractmethod

from app.domain.entities.user import User, UserCredentials, UserSession


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> UserCredentials | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def insert(self, email: str, password_hash: str, first_name: str, last_name: str) -> User:
        """Raises EmailAlreadyUsedError when the email exists."""

    @abstractmethod
    async def save_session(self, session: UserSession) -> None:
        """Create or replace the session of session.user_id."""

    @abstractmethod
    async def find_session(self, user_id: int) -> UserSession | None: ...

    @abstractmethod
    async def delete_session(self, user_id: int) -> None: ...

    @abstractmethod
    async def get_permission(self, user_id: int) -> str | None: ...
