"""Small admin commands.

uv run python -m app.infrastructure.cli grant-permission user@example.com admin
"""

import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.config.settings import get_settings
from app.infrastructure.database.mongodb import create_mongo_database
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


SAMPLE_PRODUCTS = [
    ("Mirrorless Camera", 32900.0, True),
    ("50mm f/1.8 Lens", 7490.0, True),
    ("Carbon Tripod", 4290.0, False),
    ("ND Filter Kit", 1590.0, True),
    ("Camera Backpack", 2390.0, True),
]


async def seed_products() -> None:
    settings = get_settings()
    client, db = create_mongo_database(settings.mongodb_db_atlas_uri, settings.mongodb_db_name)
    if client is None or db is None:
        raise SystemExit("GOAPP_MONGODB_DB_ATLAS_URI is not set")
    if await db.products.count_documents({}) == 0:
        now = datetime.now(UTC)
        await db.products.insert_many(
            [{"name": n, "price": p, "in_stock": s, "created_at": now} for n, p, s in SAMPLE_PRODUCTS]
        )
    print(f"products: {await db.products.count_documents({})}")
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    grant = sub.add_parser("grant-permission")
    grant.add_argument("email")
    grant.add_argument("permission")
    sub.add_parser("seed-products")
    args = parser.parse_args()
    if args.command == "grant-permission":
        asyncio.run(grant_permission(args.email, args.permission))
    elif args.command == "seed-products":
        asyncio.run(seed_products())


if __name__ == "__main__":
    main()
