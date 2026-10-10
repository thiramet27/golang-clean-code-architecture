"""Composition root: the only place that knows every concrete class (Go: main.go + module.go)."""

from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Annotated, Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.config.crud_models import CRUD_MODELS
from app.config.settings import Settings
from app.infrastructure.database.mongodb import create_mongo_database
from app.infrastructure.database.postgres import create_engine, create_session_factory
from app.infrastructure.security.jwt_tokens import JwtTokenService
from app.infrastructure.security.password import BcryptPasswordHasher
from app.interface.repositories.crud_registry import CrudModel, RegistryResourceResolver
from app.interface.repositories.postgres.user_repository import SqlAlchemyUserRepository
from app.usecases.crud.crud_usecase import CrudUsecase
from app.usecases.monitor import MonitorUsecase
from app.usecases.user.user_usecase import UserUsecase

Doc = dict[str, Any]


# "function" scope: the session commits when the endpoint returns, *before* the response is sent.
# With FastAPI's default ("request") the commit would run after the client already got its 201.
TX_SCOPE = "function"


class Container:
    def __init__(
        self,
        settings: Settings,
        engine: AsyncEngine | None = None,
        mongo_db: AsyncIOMotorDatabase[Doc] | None = None,
        crud_models: list[CrudModel] | None = None,
    ) -> None:
        self.settings = settings
        self.engine = engine or create_engine(settings.sqlalchemy_url)
        self.session_factory = create_session_factory(self.engine)
        self.mongo_client: AsyncIOMotorClient[Doc] | None = None
        if mongo_db is None:
            self.mongo_client, mongo_db = create_mongo_database(
                settings.mongodb_db_atlas_uri, settings.mongodb_db_name
            )
        self.mongo_db = mongo_db
        self.crud_models = crud_models if crud_models is not None else CRUD_MODELS

        self.hasher = BcryptPasswordHasher()
        self.tokens = JwtTokenService(
            secret=settings.secret_key,
            issuer=settings.issuer,
            access_ttl=timedelta(seconds=settings.jwt_access_expires),
            refresh_ttl=timedelta(seconds=settings.jwt_refresh_expires),  # Go used the access TTL here
        )
        self.monitor = MonitorUsecase(settings.name, settings.version)

        # FastAPI dependencies bound to this container
        async def get_session() -> AsyncIterator[AsyncSession]:
            # One transaction per request: commit if the handler succeeds, roll back otherwise.
            async with self.session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except BaseException:
                    await session.rollback()
                    raise

        def get_user_usecase(
            session: Annotated[AsyncSession, Depends(get_session, scope=TX_SCOPE)],
        ) -> UserUsecase:
            return UserUsecase(SqlAlchemyUserRepository(session), self.hasher, self.tokens)

        def get_crud_usecase(
            session: Annotated[AsyncSession, Depends(get_session, scope=TX_SCOPE)],
        ) -> CrudUsecase:
            return CrudUsecase(RegistryResourceResolver(self.crud_models, session, self.mongo_db))

        def get_monitor_usecase() -> MonitorUsecase:
            return self.monitor

        self.get_session = get_session
        self.get_user_usecase = get_user_usecase
        self.get_crud_usecase = get_crud_usecase
        self.get_monitor_usecase = get_monitor_usecase

    async def close(self) -> None:
        await self.engine.dispose()
        if self.mongo_client is not None:
            self.mongo_client.close()
