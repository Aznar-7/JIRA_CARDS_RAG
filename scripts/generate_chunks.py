import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
CHUNKS_DIR = BASE_DIR / "data" / "chunks"
SYNC_DIR = BASE_DIR / "data" / "sync"
CHANGED_FILE = SYNC_DIR / "changed_issues.json"

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


def value_or_dash(value):
    if value is None:
        return "-"
    if value == "":
        return "-"
    if value == []:
        return "-"
    return value


def load_changed_issue_keys():
    if not CHANGED_FILE.exists():
        return None

    with open(CHANGED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_metadata(issue, chunk_type):
    return {
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
        "resolved_by_inferred": issue.get("resolved_by_inferred"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "resolved_at": issue.get("resolved_at"),
        "jira_url": issue.get("jira_url"),
        "chunk_type": chunk_type,
    }


def make_chunk(issue, chunk_type, text):
    if not text or not str(text).strip():
        return None

    issue_key = issue.get("issue_key")

    return {
        "id": f"{issue_key}::{chunk_type}",
        "issue_key": issue_key,
        "chunk_type": chunk_type,
        "text": str(text).strip(),
        "metadata": build_metadata(issue, chunk_type),
    }


def generate_chunks_for_issue(issue):
    chunks = []

    issue_key = value_or_dash(issue.get("issue_key"))
    title = value_or_dash(issue.get("title"))

    general_text = f"""
Tarjeta: {issue_key}
Título: {title}
Tipo: {value_or_dash(issue.get("issue_type"))}
Estado: {value_or_dash(issue.get("status"))}
Prioridad: {value_or_dash(issue.get("priority"))}
Sprint: {value_or_dash(issue.get("sprint"))}
Ticket GLPI: {value_or_dash(issue.get("glpi_ticket"))}
Área de enfoque: {value_or_dash(issue.get("focus_area"))}
Responsable actual: {value_or_dash(issue.get("assignee"))}
Solicitante / Reporter: {value_or_dash(issue.get("reporter"))}
Resolutor inferido: {value_or_dash(issue.get("resolved_by_inferred"))}
Fecha creación: {value_or_dash(issue.get("created_at"))}
Fecha actualización: {value_or_dash(issue.get("updated_at"))}
Fecha resolución: {value_or_dash(issue.get("resolved_at"))}
Link Jira: {value_or_dash(issue.get("jira_url"))}
""".strip()

    chunks.append(make_chunk(issue, "general", general_text))

    description_text = f"""
Tarjeta {issue_key} - {title}

Descripción original:
{value_or_dash(issue.get("description"))}
""".strip()

    chunks.append(make_chunk(issue, "description", description_text))

    comments = issue.get("comments") or []
    for index, comment in enumerate(comments, start=1):
        comment_text = f"""
Tarjeta {issue_key} - {title}
Comentario {index}
Autor: {value_or_dash(comment.get("author"))}
Fecha creación: {value_or_dash(comment.get("created_at"))}
Fecha actualización: {value_or_dash(comment.get("updated_at"))}

Contenido:
{value_or_dash(comment.get("body"))}
""".strip()

        chunks.append(make_chunk(issue, f"comment_{index}", comment_text))

    attachments = issue.get("attachments") or []
    if attachments:
        attachment_lines = []

        for attachment in attachments:
            attachment_lines.append(
                f"""
Archivo: {value_or_dash(attachment.get("filename"))}
Tipo: {value_or_dash(attachment.get("mime_type"))}
Es imagen: {"Sí" if attachment.get("is_image") else "No"}
Autor: {value_or_dash(attachment.get("author"))}
Fecha: {value_or_dash(attachment.get("created_at"))}
URL: {value_or_dash(attachment.get("content_url"))}
""".strip()
            )

        attachments_text = f"""
Tarjeta {issue_key} - {title}

Adjuntos / imágenes:
{chr(10).join(attachment_lines)}

Nota: estos adjuntos todavía no fueron analizados visualmente. En una etapa posterior, las imágenes podrán procesarse con OCR o modelo multimodal para generar descripciones textuales indexables.
""".strip()

        chunks.append(make_chunk(issue, "attachments", attachments_text))

    history = issue.get("history") or []
    if history:
        history_lines = []

        for item in history:
            history_lines.append(
                f"{value_or_dash(item.get('created_at'))} | {value_or_dash(item.get('author'))} | {value_or_dash(item.get('field'))}: {value_or_dash(item.get('from'))} -> {value_or_dash(item.get('to'))}"
            )

        history_text = f"""
Tarjeta {issue_key} - {title}

Historial de cambios:
{chr(10).join(history_lines)}
""".strip()

        chunks.append(make_chunk(issue, "history", history_text))

    issue_links = issue.get("issue_links") or []
    if issue_links:
        link_lines = []

        for link in issue_links:
            link_lines.append(
                f"{value_or_dash(link.get('direction'))} | {value_or_dash(link.get('type'))} | {value_or_dash(link.get('issue_key'))} | {value_or_dash(link.get('status'))} | {value_or_dash(link.get('summary'))}"
            )

        links_text = f"""
Tarjeta {issue_key} - {title}

Tarjetas relacionadas:
{chr(10).join(link_lines)}
""".strip()

        chunks.append(make_chunk(issue, "issue_links", links_text))

    subtasks = issue.get("subtasks") or []
    if subtasks:
        subtask_lines = []

        for subtask in subtasks:
            subtask_lines.append(
                f"{value_or_dash(subtask.get('issue_key'))} | {value_or_dash(subtask.get('status'))} | {value_or_dash(subtask.get('summary'))}"
            )

        subtasks_text = f"""
Tarjeta {issue_key} - {title}

Subtareas:
{chr(10).join(subtask_lines)}
""".strip()

        chunks.append(make_chunk(issue, "subtasks", subtasks_text))

    return [chunk for chunk in chunks if chunk]


def main():
    changed_issue_keys = load_changed_issue_keys()

    if changed_issue_keys is not None:
        if not changed_issue_keys:
            print("No hay tarjetas nuevas o modificadas para generar chunks.")
            return

        normalized_files = [
            NORMALIZED_DIR / f"{issue_key}.json"
            for issue_key in changed_issue_keys
            if (NORMALIZED_DIR / f"{issue_key}.json").exists()
        ]

        print(f"Generando chunks solo para tarjetas modificadas: {len(normalized_files)}")
    else:
        normalized_files = list(NORMALIZED_DIR.glob("*.json"))
        print("No existe changed_issues.json. Generando chunks de todo.")

    if not normalized_files:
        print("No hay archivos normalizados para generar chunks.")
        return

    for normalized_file in normalized_files:
        with open(normalized_file, "r", encoding="utf-8") as f:
            issue = json.load(f)

        issue_key = issue.get("issue_key")
        chunks = generate_chunks_for_issue(issue)

        output_file = CHUNKS_DIR / f"{issue_key}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        print(f"Chunks generados {issue_key}: {len(chunks)} chunks -> {output_file}")

    print("\nGeneración de chunks finalizada.")


if __name__ == "__main__":
    main()