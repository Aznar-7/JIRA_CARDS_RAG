# db/connection.py
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async

from core.config import settings

_pool: AsyncConnectionPool | None = None


async def open_pool() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = AsyncConnectionPool(
        conninfo=settings.db_url,
        open=False,
        configure=register_vector_async,
    )
    await _pool.open()


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    if _pool is None:
        raise RuntimeError("Pool not initialized — call open_pool() first")
    async with _pool.connection() as conn:
        yield conn
