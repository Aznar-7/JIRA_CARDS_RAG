import json
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"

NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)


def get_display_name(user_obj):
    if not user_obj:
        return None

    return user_obj.get("displayName") or user_obj.get("name") or user_obj.get("emailAddress")


def extract_sprint_name(sprint_field):
    """
    Sprint puede venir como lista, objeto o None según configuración de Jira.
    """
    if not sprint_field:
        return None

    if isinstance(sprint_field, list):
        if not sprint_field:
            return None

        # Tomamos el último sprint, normalmente el más reciente/relevante
        last_sprint = sprint_field[-1]

        if isinstance(last_sprint, dict):
            return last_sprint.get("name")

        return str(last_sprint)

    if isinstance(sprint_field, dict):
        return sprint_field.get("name")

    return str(sprint_field)


def extract_description_text(description):
    """
    Jira Cloud suele traer description en formato ADF:
    {
      "type": "doc",
      "content": [...]
    }

    Esta función hace una extracción simple de texto.
    Después la mejoramos.
    """
    if not description:
        return None

    if isinstance(description, str):
        return description

    texts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(description)

    return "\n".join(t for t in texts if t).strip() or None


def normalize_issue(issue):
    fields = issue.get("fields", {})

    issue_key = issue.get("key")

    status = fields.get("status") or {}
    issue_type = fields.get("issuetype") or {}
    priority = fields.get("priority") or {}

    # Campos custom detectados en tu Jira
    sprint_field = fields.get("customfield_10020")
    glpi_ticket = fields.get("customfield_10270")

    normalized = {
        "issue_key": issue_key,
        "title": fields.get("summary"),
        "issue_type": issue_type.get("name"),
        "status": status.get("name"),
        "priority": priority.get("name"),
        "sprint": extract_sprint_name(sprint_field),
        "glpi_ticket": glpi_ticket,
        "assignee": get_display_name(fields.get("assignee")),
        "reporter": get_display_name(fields.get("reporter")),
        "creator": get_display_name(fields.get("creator")),
        "created_at": fields.get("created"),
        "updated_at": fields.get("updated"),
        "resolved_at": fields.get("resolutiondate"),
        "description": extract_description_text(fields.get("description")),
        "labels": fields.get("labels") or [],
        "components": [c.get("name") for c in fields.get("components", [])],
        "jira_url": f"{JIRA_BASE_URL}/browse/{issue_key}",
        "raw_file": f"data/raw/{issue_key}.json",
    }

    return normalized


def main():
    raw_files = list(RAW_DIR.glob("*.json"))

    if not raw_files:
        print("No hay archivos raw para normalizar.")
        return

    for raw_file in raw_files:
        with open(raw_file, "r", encoding="utf-8") as f:
            issue = json.load(f)

        normalized = normalize_issue(issue)

        issue_key = normalized["issue_key"]
        output_file = NORMALIZED_DIR / f"{issue_key}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)

        print(f"Normalizada {issue_key}: {output_file}")

    print("\nNormalización finalizada.")


if __name__ == "__main__":
    main()