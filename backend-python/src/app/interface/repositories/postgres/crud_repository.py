from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.crud import DataSchema, PageRequest, Record
from app.domain.errors import ValidationError
from app.domain.repositories.crud_repository import CrudRepository
from app.interface.repositories.postgres.models import Base
from app.interface.repositories.schema import avro_type, cast_filter_value, record_schema
from app.shared.converter import to_crud_slug


class SqlAlchemyCrudRepository(CrudRepository):
    def __init__(self, session: AsyncSession, model: type[Base]) -> None:
        self._session = session
        self._model = model
        mapper = inspect(model)
        self._columns = {c.key: c for c in mapper.columns if c.key not in model.hidden_fields}
        self._types = {key: avro_type(self._python_type(col)) for key, col in self._columns.items()}
        self._pk = mapper.primary_key[0]

    async def get_one_by_id(self, record_id: str) -> Record | None:
        try:
            pk_value = cast_filter_value(record_id, avro_type(self._python_type(self._pk)))
        except ValueError:
            return None
        row = await self._session.get(self._model, pk_value)
        return self._to_record(row) if row else None

    async def get_list(self, page: PageRequest, filters: dict[str, Any]) -> tuple[list[Record], int]:
        conditions = [self._columns[k] == v for k, v in self._parse_filters(filters).items()]
        total = await self._session.scalar(select(func.count()).select_from(self._model).where(*conditions))
        rows = await self._session.scalars(
            select(self._model)
            .where(*conditions)
            .order_by(self._pk)
            .offset(page.offset)
            .limit(page.page_size)
        )
        return [self._to_record(r) for r in rows], total or 0

    def describe(self) -> DataSchema:
        return record_schema(to_crud_slug(self._model.__name__), list(self._types.items()))

    def _parse_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        parsed = {}
        for key, raw in filters.items():
            # Only real, visible columns can be filtered: no filtering on password, no injection via keys.
            if key not in self._columns:
                raise ValidationError(f"cannot filter by '{key}'")
            try:
                parsed[key] = cast_filter_value(raw, self._types[key])
            except ValueError as e:
                raise ValidationError(f"invalid value for '{key}': {raw}") from e
        return parsed

    def _to_record(self, row: Base) -> Record:
        record = {key: getattr(row, key) for key in self._columns}
        for key, value in record.items():
            # SQLite returns naive datetimes; stored values are always UTC.
            if isinstance(value, datetime) and value.tzinfo is None:
                record[key] = value.replace(tzinfo=UTC)
        return record

    @staticmethod
    def _python_type(column: Any) -> type | None:
        try:
            return column.type.python_type  # type: ignore[no-any-return]
        except NotImplementedError:
            return None
