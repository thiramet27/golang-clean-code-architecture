import pytest

from app.shared.converter import to_crud_slug


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("users", "users"),
        ("user_permissions", "user-permissions"),
        ("UserPermissionModel", "user-permission-model"),
    ],
)
def test_slug_matches_go_version(name: str, slug: str) -> None:
    assert to_crud_slug(name) == slug
