import json
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")

# Config de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
SYNC_DIR = BASE_DIR / "data" / "sync"
CHANGED_FILE = SYNC_DIR / "changed_issues.json"

NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

# Crear los directorios si no existen
def load_changed_issue_keys():
    if not CHANGED_FILE.exists():
        return None

    with open(CHANGED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Extraer nombre del user
def get_display_name(user_obj):
    if not user_obj:
        return None

    return (
        user_obj.get("displayName")
        or user_obj.get("name")
        or user_obj.get("emailAddress")
        or user_obj.get("accountId")
    )


# Extraer nombre del sprint de la tarjeta
def extract_sprint_name(sprint_field):
    """
    Sprint puede venir como lista, objeto o None según configuración de Jira., Podrian ponerlo estandard los culiados.
    """
    if not sprint_field:
        return None

    if isinstance(sprint_field, list):
        if not sprint_field:
            return None

        last_sprint = sprint_field[-1]

        if isinstance(last_sprint, dict):
            return last_sprint.get("name")

        return str(last_sprint)

    if isinstance(sprint_field, dict):
        return sprint_field.get("name")

    return str(sprint_field)


# Extraer Texto de la Descripción
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


# Normalizar los comentarios, porque la gente habla giladas
def normalize_comments(fields):
    comment_block = fields.get("comment") or {}
    comments = comment_block.get("comments") or []

    normalized_comments = []

    for comment in comments:
        normalized_comments.append({
            "id": comment.get("id"),
            "author": get_display_name(comment.get("author")),
            "created_at": comment.get("created"),
            "updated_at": comment.get("updated"),
            "body": extract_description_text(comment.get("body")),
        })

    return normalized_comments


# Limpiar los attachments, sacar links de imagenes u otros archivos
def normalize_attachments(fields):
    attachments = fields.get("attachment") or []
    normalized_attachments = []

    for attachment in attachments:
        normalized_attachments.append({
            "id": attachment.get("id"),
            "filename": attachment.get("filename"),
            "mime_type": attachment.get("mimeType"),
            "size": attachment.get("size"),
            "author": get_display_name(attachment.get("author")),
            "created_at": attachment.get("created"),
            "content_url": attachment.get("content"),
            "thumbnail_url": attachment.get("thumbnail"),
            "is_image": (attachment.get("mimeType") or "").startswith("image/"),
        })

    return normalized_attachments


# Links a otras tarjetas
def normalize_issue_links(fields):
    issue_links = fields.get("issuelinks") or []
    normalized_links = []

    for link in issue_links:
        link_type = link.get("type") or {}

        inward_issue = link.get("inwardIssue")
        outward_issue = link.get("outwardIssue")

        if inward_issue:
            normalized_links.append({
                "direction": "inward",
                "type": link_type.get("inward"),
                "issue_key": inward_issue.get("key"),
                "summary": (inward_issue.get("fields") or {}).get("summary"),
                "status": ((inward_issue.get("fields") or {}).get("status") or {}).get("name"),
            })

        if outward_issue:
            normalized_links.append({
                "direction": "outward",
                "type": link_type.get("outward"),
                "issue_key": outward_issue.get("key"),
                "summary": (outward_issue.get("fields") or {}).get("summary"),
                "status": ((outward_issue.get("fields") or {}).get("status") or {}).get("name"),
            })

    return normalized_links


# Extraer las subtareas asi sabemos si rompieron un bicho grande en bichos mas chicos
def normalize_subtasks(fields):
    subtasks = fields.get("subtasks") or []

    return [
        {
            "issue_key": subtask.get("key"),
            "summary": (subtask.get("fields") or {}).get("summary"),
            "status": ((subtask.get("fields") or {}).get("status") or {}).get("name"),
        }
        for subtask in subtasks
    ]


# Limpiar el historial (changelog) asi chusmeamos que hicieron
def normalize_changelog(issue):
    changelog = issue.get("changelog") or {}
    histories = changelog.get("histories") or []

    normalized_history = []

    for history in histories:
        author = get_display_name(history.get("author"))
        created_at = history.get("created")

        for item in history.get("items") or []:
            normalized_history.append({
                "author": author,
                "created_at": created_at,
                "field": item.get("field"),
                "from": item.get("fromString"),
                "to": item.get("toString"),
            })

    return normalized_history


# Inferir quien resolvio el ticket por el historial de cambios (porque aveces el assignee no es el que lo resolvio)
def infer_resolved_by(history):
    """
    Intenta inferir quién resolvió mirando quién movió la tarjeta a un estado final.
    No es 100% exacto, pero sirve como aproximación auditable.
    """
    final_status_keywords = [
        "finalizada",
        "done",
        "resuelta",
        "resolved",
        "closed",
        "cerrada"
    ]

    for item in reversed(history):
        if (item.get("field") or "").lower() == "status":
            to_status = (item.get("to") or "").lower()

            if any(keyword in to_status for keyword in final_status_keywords):
                return item.get("author")

    return None


# Función Principal de Normalización
def normalize_issue(issue):
    fields = issue.get("fields", {})

    issue_key = issue.get("key")

    status = fields.get("status") or {}
    issue_type = fields.get("issuetype") or {}
    priority = fields.get("priority") or {}

    # Campos custom detectados en tu Jira
    sprint_field = fields.get("customfield_10020")
    glpi_ticket = fields.get("customfield_10270")
    focus_area = fields.get("customfield_10237")

    comments = normalize_comments(fields)
    attachments = normalize_attachments(fields)
    issue_links = normalize_issue_links(fields)
    subtasks = normalize_subtasks(fields)
    history = normalize_changelog(issue)
    inferred_resolved_by = infer_resolved_by(history)

    normalized = {
        "issue_key": issue_key,
        "title": fields.get("summary"),
        "issue_type": issue_type.get("name"),
        "status": status.get("name"),
        "priority": priority.get("name"),
        "sprint": extract_sprint_name(sprint_field),
        "glpi_ticket": glpi_ticket,
        "focus_area": focus_area,
        "assignee": get_display_name(fields.get("assignee")),
        "reporter": get_display_name(fields.get("reporter")),
        "creator": get_display_name(fields.get("creator")),
        "resolved_by_inferred": inferred_resolved_by,
        "created_at": fields.get("created"),
        "updated_at": fields.get("updated"),
        "resolved_at": fields.get("resolutiondate"),
        "description": extract_description_text(fields.get("description")),
        "labels": fields.get("labels") or [],
        "components": [c.get("name") for c in fields.get("components", [])],
        "comments": comments,
        "attachments": attachments,
        "issue_links": issue_links,
        "subtasks": subtasks,
        "history": history,
        "jira_url": f"{JIRA_BASE_URL}/browse/{issue_key}",
        "raw_file": f"data/raw/{issue_key}.json",
    }

    return normalized


# Ejecutar todo este bondi de normalización
def main():
    changed_issue_keys = load_changed_issue_keys()

    if changed_issue_keys is not None:
        if not changed_issue_keys:
            print("No hay tarjetas nuevas o modificadas para normalizar.")
            return

        raw_files = [
            RAW_DIR / f"{issue_key}.json"
            for issue_key in changed_issue_keys
            if (RAW_DIR / f"{issue_key}.json").exists()
        ]

        print(f"Normalizando solo tarjetas modificadas: {len(raw_files)}")
    else:
        raw_files = list(RAW_DIR.glob("*.json"))
        print("No existe changed_issues.json. Normalizando todo.")

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