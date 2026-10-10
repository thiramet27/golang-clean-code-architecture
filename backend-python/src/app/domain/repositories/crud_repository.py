from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.entities.crud import DataSchema, PageRequest, Record


class CrudRepository(ABC):
    """Generic read access to one data model (a Postgres table or a Mongo collection)."""

    @abstractmethod
    async def get_one_by_id(self, record_id: str) -> Record | None: ...

    @abstractmethod
    async def get_list(self, page: PageRequest, filters: dict[str, Any]) -> tuple[list[Record], int]:
        """Return (records of the page, total records matching filters)."""

    @abstractmethod
    def describe(self) -> DataSchema: ...


@dataclass(frozen=True)
class CrudResource:
    slug: str
    repository: CrudRepository
    # None = any logged-in user can read it
    required_permission: str | None = None


class CrudResourceResolver(Protocol):
    def resolve(self, slug: str) -> CrudResource:
        """Raises EntityModelNotFoundError for unknown or non-exposed slugs."""
        ...
