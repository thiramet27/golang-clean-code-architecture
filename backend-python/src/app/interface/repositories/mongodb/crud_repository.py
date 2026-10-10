from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.domain.entities.crud import DataSchema, PageRequest, Record
from app.domain.errors import ValidationError
from app.domain.repositories.crud_repository import CrudRepository
from app.interface.repositories.schema import cast_filter_value, record_schema

Doc = dict[str, Any]


class MotorCrudRepository(CrudRepository):
    def __init__(
        self,
        collection: AsyncIOMotorCollection[Doc],
        schema_name: str,
        fields: dict[str, str],
        hidden_fields: frozenset[str] = frozenset(),
    ) -> None:
        self._collection = collection
        self._schema_name = schema_name
        self._fields = {k: v for k, v in fields.items() if k not in hidden_fields}
        self._hidden = hidden_fields

    async def get_one_by_id(self, record_id: str) -> Record | None:
        try:
            object_id = ObjectId(record_id)
        except InvalidId:
            return None
        doc = await self._collection.find_one({"_id": object_id})
        return self._to_record(doc) if doc else None

    async def get_list(self, page: PageRequest, filters: dict[str, Any]) -> tuple[list[Record], int]:
        query = self._parse_filters(filters)
        cursor = self._collection.find(query).sort("_id", 1).skip(page.offset).limit(page.page_size)
        docs = await cursor.to_list(length=page.page_size)
        total = await self._collection.count_documents(query)
        return [self._to_record(d) for d in docs], total

    def describe(self) -> DataSchema:
        return record_schema(self._schema_name, [("_id", "string"), *self._fields.items()])

    def _parse_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        query: dict[str, Any] = {}
        for key, raw in filters.items():
            # Whitelisting keys also blocks operator injection such as ?$where=...
            if key not in self._fields:
                raise ValidationError(f"cannot filter by '{key}'")
            try:
                query[key] = cast_filter_value(raw, self._fields[key])
            except ValueError as e:
                raise ValidationError(f"invalid value for '{key}': {raw}") from e
        return query

    def _to_record(self, doc: dict[str, Any]) -> Record:
        record = {k: v for k, v in doc.items() if k not in self._hidden}
        record["_id"] = str(doc["_id"])
        return record
