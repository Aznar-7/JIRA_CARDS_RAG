# scripts/transform/ingest_to_db.py
"""
Reads normalized issues and chunks from local files, generates embeddings,
and upserts everything into PostgreSQL + pgvector.

Usage:
    python scripts/transform/ingest_to_db.py
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import psycopg
from pgvector.psycopg import register_vector

from core.config import settings
from rag.embeddings import embed_texts

BASE_DIR = Path(__file__).resolve().parent.parent.parent
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
CHUNKS_DIR = BASE_DIR / "data" / "chunks"


def load_normalized_issues() -> list[dict]:
    issues = []
    for path in sorted(NORMALIZED_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            issues.append(json.load(f))
    return issues


def load_chunks_for_issue(issue_key: str) -> list[dict]:
    path = CHUNKS_DIR / f"{issue_key}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ingest_all() -> None:
    issues = load_normalized_issues()
    if not issues:
        print("No normalized issues found. Run the pipeline first.")
        return

    print(f"Found {len(issues)} normalized issues.")

    with psycopg.connect(settings.db_url) as conn:
        register_vector(conn)

        for issue in issues:
            issue_key = issue["issue_key"]
            print(f"  Ingesting {issue_key}...")

            chunks = load_chunks_for_issue(issue_key)
            if not chunks:
                print(f"    No chunks found for {issue_key}, skipping.")
                continue

            texts = [c["text"] for c in chunks]
            embeddings = embed_texts(texts, show_progress=True)

            with conn.cursor() as cur:
                # Upsert issue
                cur.execute(
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
                        title = EXCLUDED.title, status = EXCLUDED.status,
                        sprint = EXCLUDED.sprint, assignee = EXCLUDED.assignee,
                        updated_at = EXCLUDED.updated_at, ingested_at = NOW()
                    """,
                    {
                        "issue_key": issue["issue_key"],
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
                # Delete + re-insert chunks atomically
                cur.execute("DELETE FROM chunks WHERE issue_key = %s", [issue_key])
                cur.executemany(
                    """
                    INSERT INTO chunks (chunk_id, issue_key, chunk_type, text, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            chunk["id"],
                            chunk["issue_key"],
                            chunk["chunk_type"],
                            chunk["text"],
                            embedding,
                            json.dumps(chunk.get("metadata", {})),
                        )
                        for chunk, embedding in zip(chunks, embeddings)
                    ],
                )
            conn.commit()
            print(f"    {len(chunks)} chunks ingested.")

    print("\nIngest complete.")


if __name__ == "__main__":
    try:
        ingest_all()
    except Exception as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        sys.exit(1)
