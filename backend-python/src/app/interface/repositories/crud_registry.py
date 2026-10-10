from dataclasses import dataclass, field
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import EntityModelNotFoundError
from app.domain.repositories.crud_repository import CrudRepository, CrudResource
from app.interface.repositories.mongodb.crud_repository import MotorCrudRepository
from app.interface.repositories.postgres.crud_repository import SqlAlchemyCrudRepository
from app.interface.repositories.postgres.models import Base
from app.shared.converter import to_crud_slug

Doc = dict[str, Any]


@dataclass(frozen=True)
class PostgresCrudModel:
    model: type[Base]
    required_permission: str | None = None
    exposed: bool = True

    @property
    def slug(self) -> str:
        return to_crud_slug(self.model.__tablename__)


@dataclass(frozen=True)
class MongoCrudModel:
    name: str  # used as the schema name, like the Go struct name
    collection: str
    fields: dict[str, str]  # field -> avro type
    hidden_fields: frozenset[str] = field(default_factory=frozenset)
    required_permission: str | None = None
    exposed: bool = True

    @property
    def slug(self) -> str:
        return to_crud_slug(self.collection)


CrudModel = PostgresCrudModel | MongoCrudModel


class RegistryResourceResolver:
    """Turns a URL slug into a repository, the Python version of GetCRUDRepository()."""

    def __init__(
        self,
        models: list[CrudModel],
        session: AsyncSession,
        mongo_db: AsyncIOMotorDatabase[Doc] | None = None,
    ) -> None:
        self._models = {m.slug: m for m in models if m.exposed}
        self._session = session
        self._mongo_db = mongo_db

    def resolve(self, slug: str) -> CrudResource:
        model = self._models.get(slug)
        if model is None:
            raise EntityModelNotFoundError(slug)

        repository: CrudRepository
        if isinstance(model, PostgresCrudModel):
            repository = SqlAlchemyCrudRepository(self._session, model.model)
        else:
            if self._mongo_db is None:
                raise EntityModelNotFoundError(f"{slug} (MongoDB is not configured)")
            repository = MotorCrudRepository(
                self._mongo_db[model.collection], to_crud_slug(model.name), model.fields, model.hidden_fields
            )
        return CrudResource(slug=slug, repository=repository, required_permission=model.required_permission)
