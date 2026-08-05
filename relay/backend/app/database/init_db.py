from sqlalchemy.ext.asyncio import AsyncEngine

import app.models  # noqa: F401
from app.database.base import Base
from app.database.session import engine


async def init_db(database_engine: AsyncEngine = engine) -> None:
    """
    Create all registered Relay database tables.

    This is intended for local development and early hackathon setup.
    Alembic migrations will become the authoritative schema mechanism later.
    """

    async with database_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)