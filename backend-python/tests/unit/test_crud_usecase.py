from typing import Any

import pytest

from app.domain.entities.crud import DataSchema, PageRequest, Record
from app.domain.errors import EntityModelNotFoundError, NotFoundError, PermissionDeniedError
from app.domain.repositories.crud_repository import CrudRepository, CrudResource
from app.usecases.crud.crud_usecase import CrudUsecase

ROWS = [{"id": i, "name": f"row {i}"} for i in range(1, 26)]


class ListRepository(CrudRepository):
    async def get_one_by_id(self, record_id: str) -> Record | None:
        return next((r for r in ROWS if str(r["id"]) == record_id), None)

    async def get_list(self, page: PageRequest, filters: dict[str, Any]) -> tuple[list[Record], int]:
        return ROWS[page.offset : page.offset + page.page_size], len(ROWS)

    def describe(self) -> DataSchema:
        return {"type": "record", "name": "row", "fields": []}


class Resolver:
    def resolve(self, slug: str) -> CrudResource:
        if slug == "rows":
            return CrudResource("rows", ListRepository())
        if slug == "secrets":
            return CrudResource("secrets", ListRepository(), required_permission="admin")
        raise EntityModelNotFoundError(slug)


usecase = CrudUsecase(Resolver())


async def test_list_counts_pages_from_total_not_from_page_size() -> None:
    # Go bug: total_data used RowsAffected of the current page
    result = await usecase.retrieve_list(None, "rows", PageRequest(page=3, page_size=10), {})
    assert (len(result.data), result.total_data, result.total_page) == (5, 25, 3)


@pytest.mark.parametrize(
    ("page", "expected"), [(PageRequest(0, 0), (1, 10)), (PageRequest(-5, 5000), (1, 1000))]
)
async def test_page_values_are_normalised(page: PageRequest, expected: tuple[int, int]) -> None:
    result = await usecase.retrieve_list(None, "rows", page, {})
    assert (result.page, result.page_size) == expected


async def test_permission_is_required_for_protected_models() -> None:
    with pytest.raises(PermissionDeniedError):
        await usecase.retrieve_list("staff", "secrets", PageRequest(), {})
    assert (await usecase.retrieve_list("admin", "secrets", PageRequest(), {})).total_data == 25


async def test_unknown_model_and_record() -> None:
    with pytest.raises(EntityModelNotFoundError):
        usecase.describe(None, "nope")
    with pytest.raises(NotFoundError):
        await usecase.retrieve(None, "rows", "999")
