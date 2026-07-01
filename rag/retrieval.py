# rag/retrieval.py
import psycopg

from core.config import settings
from db.repository import hybrid_search
from rag.embeddings import embed_text


async def retrieve(
    conn: psycopg.AsyncConnection,
    question: str,
    status: str | None = None,
    sprint: str | None = None,
) -> list[dict]:
    """Runs hybrid search and filters by relevance threshold."""
    embedding = embed_text(question)
    candidates = await hybrid_search(
        conn=conn,
        query_embedding=embedding,
        query_text=question,
        limit=settings.search_limit * 2,
        status=status,
        sprint=sprint,
    )
    return [c for c in candidates if c["score"] >= settings.relevance_threshold][
        : settings.search_limit
    ]
