# tests/conftest.py
import sys
from pathlib import Path
import pytest

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_raw_issue():
    """Minimal raw Jira API response with ADF description."""
    return {
        "key": "DEMO-001",
        "fields": {
            "summary": "Error en validación de facturas",
            "status": {"name": "Done"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "María López"},
            "reporter": {"displayName": "Juan García"},
            "creator": {"displayName": "Juan García"},
            "created": "2026-01-10T10:00:00.000-0300",
            "updated": "2026-01-15T18:30:00.000-0300",
            "resolutiondate": "2026-01-15T18:30:00.000-0300",
            "labels": ["billing"],
            "components": [{"name": "API"}],
            "customfield_10020": [{"name": "SPRINT-01"}],
            "customfield_10270": "GLPI-1234",
            "customfield_10237": "Backend",
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "El sistema lanza "},
                            {"type": "text", "text": "un error 500."},
                        ],
                    }
                ],
            },
            "comment": {"comments": []},
            "attachment": [],
            "issuelinks": [],
            "subtasks": [],
        },
        "changelog": {"histories": []},
    }


@pytest.fixture
def sample_normalized_issue():
    """Normalized issue as produced by scripts/transform/normalize.py."""
    return {
        "issue_key": "DEMO-001",
        "title": "Error en validación de facturas",
        "issue_type": "Bug",
        "status": "Done",
        "priority": "High",
        "sprint": "SPRINT-01",
        "glpi_ticket": "GLPI-1234",
        "focus_area": "Backend",
        "assignee": "María López",
        "reporter": "Juan García",
        "creator": "Juan García",
        "resolved_by_inferred": None,
        "created_at": "2026-01-10T10:00:00.000-0300",
        "updated_at": "2026-01-15T18:30:00.000-0300",
        "resolved_at": "2026-01-15T18:30:00.000-0300",
        "description": "Texto de prueba.",
        "labels": ["billing"],
        "components": ["API"],
        "comments": [
            {
                "id": "10001",
                "author": "María López",
                "created_at": "2026-01-12T14:00:00.000-0300",
                "updated_at": "2026-01-12T14:00:00.000-0300",
                "body": "Fix identificado.",
            }
        ],
        "attachments": [],
        "issue_links": [],
        "subtasks": [],
        "history": [
            {
                "author": "María López",
                "created_at": "2026-01-15T18:30:00.000-0300",
                "field": "status",
                "from": "In Progress",
                "to": "Done",
            }
        ],
        "jira_url": "https://example.atlassian.net/browse/DEMO-001",
        "raw_file": "data/raw/DEMO-001.json",
    }
