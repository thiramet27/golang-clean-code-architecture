"""Avro-style schema for /describe and every /data response (same shape as the Go version)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.entities.crud import DataSchema

PY_TO_AVRO: dict[type, str] = {
    str: "string",
    int: "int",
    bool: "boolean",
    float: "double",
    Decimal: "double",
    datetime: "datetime",
    date: "date",
    dict: "map",
    list: "array",
}


def avro_type(py_type: type | None) -> str:
    return PY_TO_AVRO.get(py_type, "unknown") if py_type else "unknown"


def record_schema(name: str, fields: list[tuple[str, str]]) -> DataSchema:
    return {
        "type": "record",
        "name": name,
        "fields": [{"name": field, "type": type_} for field, type_ in fields],
    }


def cast_filter_value(raw: Any, avro: str) -> Any:
    """Query strings are always text; cast them to the column type so the database compares correctly."""
    if not isinstance(raw, str):
        return raw
    match avro:
        case "int":
            return int(raw)
        case "double":
            return float(raw)
        case "boolean":
            if raw.lower() not in {"true", "false", "1", "0"}:
                raise ValueError(f"not a boolean: {raw}")
            return raw.lower() in {"true", "1"}
        case "datetime":
            return datetime.fromisoformat(raw)
        case _:
            return raw
