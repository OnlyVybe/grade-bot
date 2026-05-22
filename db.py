import asyncpg
import os

pool = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))


async def execute(query, *args):
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query, *args):
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query, *args):
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)