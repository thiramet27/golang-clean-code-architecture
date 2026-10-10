"""Models served by the generic /api/v1/data/{slug} endpoints (Go: src/config/crudModels.go).

To add a model: define it in interface/repositories/postgres/models.py (or describe the Mongo
collection here), then add one line below.
"""

from app.interface.repositories.crud_registry import CrudModel, MongoCrudModel, PostgresCrudModel
from app.interface.repositories.postgres.models import UserModel, UserPermissionModel, UserTokenModel

CRUD_MODELS: list[CrudModel] = [
    # PostgreSQL
    PostgresCrudModel(UserModel),  # password is hidden (UserModel.hidden_fields)
    PostgresCrudModel(UserPermissionModel, required_permission="admin"),
    # The Go version exposed this table, so any logged-in user could read everyone's tokens.
    PostgresCrudModel(UserTokenModel, exposed=False),
    # MongoDB (served only when GOAPP_MONGODB_DB_ATLAS_URI is set)
    MongoCrudModel(
        name="ProductModel",
        collection="products",
        fields={"name": "string", "price": "double", "in_stock": "boolean", "created_at": "datetime"},
    ),
]
