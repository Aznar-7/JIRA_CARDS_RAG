# db/connection.py
from contextlib import asynccontextmanager

import psycopg
from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async

from core.config import settings

_pool: AsyncConnectionPool | None = None


async def open_pool() -> None:
    global _pool
    _pool = AsyncConnectionPool(conninfo=settings.db_url, open=False)
    await _pool.open()


async def close_pool() -> None:
    if _pool:
        await _pool.close()


@asynccontextmanager
async def get_conn():
    """Async context manager that yields a connection from the pool
    with pgvector type adapter registered."""
    assert _pool is not None, "Pool not initialized — call open_pool() first"
    async with _pool.connection() as conn:
        await register_vector_async(conn)
        yield conn
