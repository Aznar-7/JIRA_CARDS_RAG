# api/routes/search.py
from fastapi import APIRouter

from api.schemas import SearchRequest, SearchResponse, SearchResult
from db.connection import get_conn
from db.repository import hybrid_search
from rag.embeddings import embed_text

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_chunks(request: SearchRequest):
    query_embedding = embed_text(request.query)

    async with get_conn() as conn:
        raw_results = await hybrid_search(
            conn=conn,
            query_embedding=query_embedding,
            query_text=request.query,
            limit=request.limit,
            status=request.status,
            sprint=request.sprint,
        )

    results = [
        SearchResult(
            chunk_id=r["chunk_id"],
            issue_key=r["issue_key"],
            title=r["title"],
            chunk_type=r["chunk_type"],
            text=r["text"][:500],
            score=round(r["score"], 4),
            jira_url=r["jira_url"],
            status=r["status"],
            sprint=r["sprint"],
        )
        for r in raw_results
    ]

    return SearchResponse(results=results, total=len(results))
