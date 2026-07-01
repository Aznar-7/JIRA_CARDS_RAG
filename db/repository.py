# db/repository.py
import json
import re

import numpy as np
import psycopg

from core.text import normalize_text


async def upsert_issue(conn: psycopg.AsyncConnection, issue: dict) -> None:
    await conn.execute(
        """
        INSERT INTO issues (
            issue_key, title, issue_type, status, priority, sprint,
            glpi_ticket, focus_area, assignee, reporter, resolved_by,
            created_at, updated_at, resolved_at, jira_url
        ) VALUES (
            %(issue_key)s, %(title)s, %(issue_type)s, %(status)s,
            %(priority)s, %(sprint)s, %(glpi_ticket)s, %(focus_area)s,
            %(assignee)s, %(reporter)s, %(resolved_by)s,
            %(created_at)s, %(updated_at)s, %(resolved_at)s, %(jira_url)s
        )
        ON CONFLICT (issue_key) DO UPDATE SET
            title         = EXCLUDED.title,
            issue_type    = EXCLUDED.issue_type,
            status        = EXCLUDED.status,
            priority      = EXCLUDED.priority,
            sprint        = EXCLUDED.sprint,
            glpi_ticket   = EXCLUDED.glpi_ticket,
            focus_area    = EXCLUDED.focus_area,
            assignee      = EXCLUDED.assignee,
            reporter      = EXCLUDED.reporter,
            resolved_by   = EXCLUDED.resolved_by,
            updated_at    = EXCLUDED.updated_at,
            resolved_at   = EXCLUDED.resolved_at,
            jira_url      = EXCLUDED.jira_url,
            ingested_at   = NOW()
        """,
        {
            "issue_key": issue.get("issue_key"),
            "title": issue.get("title"),
            "issue_type": issue.get("issue_type"),
            "status": issue.get("status"),
            "priority": issue.get("priority"),
            "sprint": issue.get("sprint"),
            "glpi_ticket": issue.get("glpi_ticket"),
            "focus_area": issue.get("focus_area"),
            "assignee": issue.get("assignee"),
            "reporter": issue.get("reporter"),
            "resolved_by": issue.get("resolved_by_inferred"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "resolved_at": issue.get("resolved_at"),
            "jira_url": issue.get("jira_url"),
        },
    )


async def upsert_chunks(
    conn: psycopg.AsyncConnection,
    issue_key: str,
    chunks: list[dict],
    embeddings: np.ndarray,
) -> None:
    # Delete existing chunks for this issue before re-inserting
    await conn.execute("DELETE FROM chunks WHERE issue_key = %s", [issue_key])

    for chunk, embedding in zip(chunks, embeddings):
        await conn.execute(
            """
            INSERT INTO chunks (chunk_id, issue_key, chunk_type, text, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                chunk["id"],
                chunk["issue_key"],
                chunk["chunk_type"],
                chunk["text"],
                embedding,
                json.dumps(chunk.get("metadata", {})),
            ],
        )


async def hybrid_search(
    conn: psycopg.AsyncConnection,
    query_embedding: np.ndarray,
    query_text: str,
    limit: int = 10,
    status: str | None = None,
    sprint: str | None = None,
) -> list[dict]:
    filters = []
    params: list = [query_embedding, limit * 3]

    if status:
        filters.append(f"metadata->>'status' ILIKE %s")
        params.append(f"%{status}%")
    if sprint:
        filters.append(f"metadata->>'sprint' ILIKE %s")
        params.append(f"%{sprint}%")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    rows = await conn.execute(
        f"""
        SELECT chunk_id, issue_key, chunk_type, text, metadata,
               1 - (embedding <=> %s::vector) AS sem_score
        FROM chunks
        {where}
        ORDER BY sem_score DESC
        LIMIT %s
        """,
        params,
    )
    rows = await rows.fetchall()

    # Apply simple keyword boost in Python
    terms = [t for t in re.findall(r"\w+", normalize_text(query_text)) if len(t) > 2]

    results = []
    for row in rows:
        sem_score = float(row[5])
        text_lower = normalize_text(row[3] or "")
        meta = row[4] or {}
        issue_key_lower = normalize_text(meta.get("issue_key", ""))

        lit_score = 0.0
        for term in terms:
            lit_score += text_lower.count(term) * 0.03
            if term in issue_key_lower:
                lit_score += 0.5
        lit_score = min(1.0, lit_score)

        final_score = sem_score * 0.65 + lit_score * 0.35
        results.append(
            {
                "chunk_id": row[0],
                "issue_key": row[1],
                "chunk_type": row[2],
                "text": row[3],
                "metadata": meta,
                "score": final_score,
                "jira_url": meta.get("jira_url", ""),
                "title": meta.get("title", ""),
                "status": meta.get("status", ""),
                "sprint": meta.get("sprint", ""),
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]
