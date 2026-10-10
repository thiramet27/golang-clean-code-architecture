from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserCredentials, UserSession
from app.domain.errors import EmailAlreadyUsedError
from app.domain.repositories.user_repository import UserRepository
from app.interface.repositories.postgres.models import UserModel, UserPermissionModel, UserTokenModel


def _as_utc(value: datetime) -> datetime:
    # SQLite drops tzinfo; Postgres keeps it. Normalise so the domain always gets aware datetimes.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_entity(m: UserModel) -> User:
    return User(
        id=m.id,
        email=m.email,
        first_name=m.first_name,
        last_name=m.last_name,
        created_at=_as_utc(m.created_at),
        updated_at=_as_utc(m.updated_at),
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> UserCredentials | None:
        model = await self._session.scalar(select(UserModel).where(UserModel.email == email))
        return UserCredentials(user=_to_entity(model), password_hash=model.password) if model else None

    async def get_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    async def insert(self, email: str, password_hash: str, first_name: str, last_name: str) -> User:
        model = UserModel(email=email, password=password_hash, first_name=first_name, last_name=last_name)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise EmailAlreadyUsedError() from e
        await self._session.refresh(model)
        return _to_entity(model)

    async def save_session(self, session: UserSession) -> None:
        model = await self._session.scalar(
            select(UserTokenModel).where(UserTokenModel.user_id == session.user_id)
        )
        if model is None:
            model = UserTokenModel(user_id=session.user_id)
            self._session.add(model)
        model.access = session.access_digest
        model.refresh = session.refresh_digest
        await self._session.flush()

    async def find_session(self, user_id: int) -> UserSession | None:
        model = await self._session.scalar(select(UserTokenModel).where(UserTokenModel.user_id == user_id))
        if model is None:
            return None
        return UserSession(user_id=model.user_id, access_digest=model.access, refresh_digest=model.refresh)

    async def delete_session(self, user_id: int) -> None:
        await self._session.execute(delete(UserTokenModel).where(UserTokenModel.user_id == user_id))

    async def get_permission(self, user_id: int) -> str | None:
        return await self._session.scalar(
            select(UserPermissionModel.permission).where(UserPermissionModel.user_id == user_id).limit(1)
        )
