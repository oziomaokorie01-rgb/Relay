import asyncio
from sqlalchemy import inspect

from app.database.session import engine


async def check():
    async with engine.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        print(sorted(tables))


asyncio.run(check())
