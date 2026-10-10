from dataclasses import dataclass, field
from typing import Any

DataSchema = dict[str, Any]
Record = dict[str, Any]


@dataclass(frozen=True)
class DataResponse:
    data: Record
    data_schema: DataSchema
    code: int = 200
    message: str = "success"


@dataclass(frozen=True)
class DataListResponse:
    data: list[Record]
    page: int
    page_size: int
    total_page: int
    total_data: int
    data_schema: DataSchema = field(default_factory=dict)
    code: int = 200
    message: str = "success"


@dataclass(frozen=True)
class PageRequest:
    page: int = 1
    page_size: int = 10

    MAX_PAGE_SIZE = 1000

    def normalized(self) -> "PageRequest":
        size = 10 if self.page_size <= 0 else min(self.page_size, self.MAX_PAGE_SIZE)
        return PageRequest(page=max(self.page, 1), page_size=size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
