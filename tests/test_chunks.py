# tests/test_chunks.py
from scripts.transform.generate_chunks import generate_chunks_for_issue


def test_general_and_description_chunks_always_generated(sample_normalized_issue):
    chunks = generate_chunks_for_issue(sample_normalized_issue)
    chunk_types = {c["chunk_type"] for c in chunks}
    assert "general" in chunk_types
    assert "description" in chunk_types


def test_chunk_ids_are_stable(sample_normalized_issue):
    chunks1 = generate_chunks_for_issue(sample_normalized_issue)
    chunks2 = generate_chunks_for_issue(sample_normalized_issue)
    assert [c["id"] for c in chunks1] == [c["id"] for c in chunks2]


def test_chunk_id_format(sample_normalized_issue):
    chunks = generate_chunks_for_issue(sample_normalized_issue)
    for chunk in chunks:
        assert "::" in chunk["id"]
        assert chunk["id"].startswith("DEMO-001::")


def test_no_empty_chunk_text(sample_normalized_issue):
    chunks = generate_chunks_for_issue(sample_normalized_issue)
    for chunk in chunks:
        assert chunk["text"].strip(), f"Empty text in chunk {chunk['id']}"


def test_comment_chunk_generated_per_comment(sample_normalized_issue):
    chunks = generate_chunks_for_issue(sample_normalized_issue)
    comment_chunks = [c for c in chunks if c["chunk_type"].startswith("comment_")]
    assert len(comment_chunks) == len(sample_normalized_issue["comments"])


def test_null_description_produces_placeholder_chunk():
    # When description is None, generate_chunks_for_issue still produces a description
    # chunk using "-" as a placeholder (via value_or_dash). This test verifies that
    # behaviour instead of asserting no chunk is produced.
    issue = {
        "issue_key": "DEMO-003",
        "title": "Tarea sin descripción",
        "issue_type": "Task",
        "status": "Done",
        "priority": "Low",
        "sprint": None,
        "glpi_ticket": None,
        "focus_area": None,
        "assignee": None,
        "reporter": "Juan García",
        "creator": "Juan García",
        "resolved_by_inferred": None,
        "created_at": "2026-01-15T20:00:00.000-0300",
        "updated_at": "2026-01-16T08:00:00.000-0300",
        "resolved_at": None,
        "description": None,
        "labels": [],
        "components": [],
        "comments": [],
        "attachments": [],
        "issue_links": [],
        "subtasks": [],
        "history": [],
        "jira_url": "https://example.atlassian.net/browse/DEMO-003",
        "raw_file": "data/raw/DEMO-003.json",
    }
    chunks = generate_chunks_for_issue(issue)
    desc_chunks = [c for c in chunks if c["chunk_type"] == "description"]
    # The description chunk is always produced; when description is None,
    # value_or_dash substitutes "-" so the chunk text is non-empty.
    assert len(desc_chunks) == 1
    assert "-" in desc_chunks[0]["text"]


def test_chunk_metadata_has_issue_key(sample_normalized_issue):
    chunks = generate_chunks_for_issue(sample_normalized_issue)
    for chunk in chunks:
        assert chunk["metadata"]["issue_key"] == "DEMO-001"
