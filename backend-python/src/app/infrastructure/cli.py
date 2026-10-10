"""Small admin commands.

uv run python -m app.infrastructure.cli grant-permission user@example.com admin
"""

import argparse
import asyncio

from sqlalchemy import delete, select

from app.config.settings import get_settings
from app.infrastructure.database.postgres import create_engine, create_session_factory
from app.interface.repositories.postgres.models import UserModel, UserPermissionModel


async def grant_permission(email: str, permission: str) -> None:
    engine = create_engine(get_settings().sqlalchemy_url)
    async with create_session_factory(engine)() as session, session.begin():
        user_id = await session.scalar(select(UserModel.id).where(UserModel.email == email.lower()))
        if user_id is None:
            raise SystemExit(f"user not found: {email}")
        await session.execute(delete(UserPermissionModel).where(UserPermissionModel.user_id == user_id))
        session.add(UserPermissionModel(user_id=user_id, permission=permission))
    await engine.dispose()
    print(f"{email} -> {permission}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    grant = sub.add_parser("grant-permission")
    grant.add_argument("email")
    grant.add_argument("permission")
    args = parser.parse_args()
    if args.command == "grant-permission":
        asyncio.run(grant_permission(args.email, args.permission))


if __name__ == "__main__":
    main()
