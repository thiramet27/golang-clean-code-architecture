import math
from typing import Any

from app.domain.entities.crud import DataListResponse, DataResponse, DataSchema, PageRequest
from app.domain.errors import NotFoundError, PermissionDeniedError
from app.domain.repositories.crud_repository import CrudResource, CrudResourceResolver


class CrudUsecase:
    def __init__(self, resources: CrudResourceResolver) -> None:
        self._resources = resources

    async def retrieve(self, permission: str | None, slug: str, record_id: str) -> DataResponse:
        resource = self._authorized(permission, slug)
        record = await resource.repository.get_one_by_id(record_id)
        if record is None:
            raise NotFoundError(f"{slug} {record_id} not found")
        return DataResponse(data=record, data_schema=resource.repository.describe())

    async def retrieve_list(
        self, permission: str | None, slug: str, page: PageRequest, filters: dict[str, Any]
    ) -> DataListResponse:
        resource = self._authorized(permission, slug)
        page = page.normalized()
        records, total = await resource.repository.get_list(page, filters)
        return DataListResponse(
            data=records,
            page=page.page,
            page_size=page.page_size,
            total_page=math.ceil(total / page.page_size),
            total_data=total,
            data_schema=resource.repository.describe(),
        )

    def describe(self, permission: str | None, slug: str) -> DataSchema:
        return self._authorized(permission, slug).repository.describe()

    def _authorized(self, permission: str | None, slug: str) -> CrudResource:
        resource = self._resources.resolve(slug)
        if resource.required_permission and permission != resource.required_permission:
            raise PermissionDeniedError(f"permission '{resource.required_permission}' is required")
        return resource
