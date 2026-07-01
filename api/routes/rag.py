# api/routes/rag.py
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from api.schemas import RagRequest
from db.connection import get_conn
from rag.context import condense_question
from rag.generator import stream_answer
from rag.retrieval import retrieve

router = APIRouter()

_NO_EVIDENCE = (
    "No encontré información suficiente en los tickets de Jira para responder esta pregunta."
)


@router.post("/rag/query")
async def rag_query(request: RagRequest):
    history = [m.model_dump() for m in request.history]

    async def generate():
        try:
            # 1. Condense the question if there's prior conversation
            condensed = await condense_question(request.question, history)

            # 2. Retrieve relevant chunks
            async with get_conn() as conn:
                chunks = await retrieve(
                    conn=conn,
                    question=condensed,
                    status=request.status,
                    sprint=request.sprint,
                )

            # 3. Abstain immediately when no evidence passes the threshold
            if not chunks:
                yield f"data: {json.dumps({'type': 'token', 'content': _NO_EVIDENCE})}\n\n"
                yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # 4. Stream LLM answer
            async for token in stream_answer(condensed, chunks, history):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 5. Send sources after answer completes
            sources = [
                {
                    "chunk_id": c["chunk_id"],
                    "issue_key": c["issue_key"],
                    "title": c["title"],
                    "chunk_type": c["chunk_type"],
                    "jira_url": c["jira_url"],
                    "score": round(c["score"], 4),
                }
                for c in chunks
            ]
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception:
            logger.exception("rag_query stream failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'internal error'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
