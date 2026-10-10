import re


def camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def to_crud_slug(name: str) -> str:
    """UserPermissionModel -> user-permission-model, user_permissions -> user-permissions (same as Go)."""
    return camel_to_snake(name).replace("_", "-")
