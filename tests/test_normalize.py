# tests/test_normalize.py
import os
os.environ.setdefault("JIRA_BASE_URL", "https://example.atlassian.net")

from scripts.transform.normalize import (
    extract_description_text,
    normalize_issue,
    infer_resolved_by,
)


def test_extract_description_from_adf_nodes():
    adf = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "text", "text": "world"},
                ],
            }
        ],
    }
    result = extract_description_text(adf)
    assert "Hello" in result
    assert "world" in result


def test_extract_description_from_plain_string():
    assert extract_description_text("plain text") == "plain text"


def test_extract_description_none_returns_none():
    assert extract_description_text(None) is None


def test_extract_description_empty_doc_returns_none():
    adf = {"type": "doc", "content": []}
    assert extract_description_text(adf) is None


def test_normalize_issue_required_fields_present(sample_raw_issue):
    result = normalize_issue(sample_raw_issue)
    for field in ["issue_key", "title", "status", "jira_url", "comments", "history"]:
        assert field in result, f"Missing field: {field}"


def test_normalize_issue_key_matches(sample_raw_issue):
    result = normalize_issue(sample_raw_issue)
    assert result["issue_key"] == "DEMO-001"


def test_normalize_issue_sprint_extracted(sample_raw_issue):
    result = normalize_issue(sample_raw_issue)
    assert result["sprint"] == "SPRINT-01"


def test_normalize_issue_description_is_plain_text(sample_raw_issue):
    result = normalize_issue(sample_raw_issue)
    assert isinstance(result["description"], str)
    assert "El sistema lanza" in result["description"]


def test_infer_resolved_by_finds_done_transition():
    history = [
        {"author": "A", "created_at": "...", "field": "status", "from": "To Do", "to": "In Progress"},
        {"author": "B", "created_at": "...", "field": "status", "from": "In Progress", "to": "Done"},
    ]
    assert infer_resolved_by(history) == "B"


def test_infer_resolved_by_returns_none_when_no_final_status():
    history = [
        {"author": "A", "created_at": "...", "field": "status", "from": "To Do", "to": "In Progress"},
    ]
    assert infer_resolved_by(history) is None
