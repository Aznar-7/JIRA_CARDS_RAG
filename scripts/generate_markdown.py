import json
from pathlib import Path

# Config de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"
MARKDOWN_DIR = BASE_DIR / "data" / "markdown"

MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

# Funciones para generar Markdown a partir de los datos normalizados ( issue normalizado -> markdown con formato estandar para cada tarjeta)

# Funcion de formateo para evitar valores vacios o nulos en el markdown, y mostrar un guion en su lugar
def value_or_dash(value):
    if value is None:
        return "-"
    if value == "":
        return "-"
    if value == []:
        return "-"
    return value


# Funcion parecida a la anterior pero para listas, asi no quedan listas vacias o con formato raro
def list_or_dash(items):
    if not items:
        return "-"

    return ", ".join(str(item) for item in items)


# Funcion para asegurar que los textos vacios no rompan el markdown
def safe_text(value):
    """
    Evita romper el Markdown si el texto viene vacío.
    """
    return value_or_dash(value)


# Funcion para armar la seccion de comentarios con autor y fechas
def render_comments(comments):
    if not comments:
        return "No hay comentarios registrados.\n"

    lines = []

    for index, comment in enumerate(comments, start=1):
        lines.append(f"### Comentario {index}")
        lines.append("")
        lines.append(f"- **Autor:** {value_or_dash(comment.get('author'))}")
        lines.append(f"- **Creado:** {value_or_dash(comment.get('created_at'))}")
        lines.append(f"- **Actualizado:** {value_or_dash(comment.get('updated_at'))}")
        lines.append("")
        lines.append(safe_text(comment.get("body")))
        lines.append("")

    return "\n".join(lines)


# Funcion para armar la tabla de adjuntos y marcar cuales son imagenes
def render_attachments(attachments):
    if not attachments:
        return "No hay adjuntos registrados.\n"

    lines = []
    lines.append("| Archivo | Tipo | Imagen | Tamaño | Autor | Fecha | URL |")
    lines.append("|---|---|---|---:|---|---|---|")

    for attachment in attachments:
        filename = value_or_dash(attachment.get("filename"))
        mime_type = value_or_dash(attachment.get("mime_type"))
        is_image = "Sí" if attachment.get("is_image") else "No"
        size = value_or_dash(attachment.get("size"))
        author = value_or_dash(attachment.get("author"))
        created_at = value_or_dash(attachment.get("created_at"))
        content_url = value_or_dash(attachment.get("content_url"))

        lines.append(
            f"| {filename} | {mime_type} | {is_image} | {size} | {author} | {created_at} | {content_url} |"
        )

    lines.append("")
    lines.append("> Nota: en esta etapa se documentan los adjuntos y se identifica si son imágenes. En una etapa posterior se podrían descargar y procesar con OCR o un modelo multimodal para generar descripciones analizables por IA.")
    lines.append("")

    return "\n".join(lines)


# Funcion para mostrar las tarjetas relacionadas y el tipo de relacion
def render_issue_links(issue_links):
    if not issue_links:
        return "No hay tarjetas relacionadas registradas.\n"

    lines = []
    lines.append("| Dirección | Relación | Tarjeta | Estado | Resumen |")
    lines.append("|---|---|---|---|---|")

    for link in issue_links:
        lines.append(
            f"| {value_or_dash(link.get('direction'))} | "
            f"{value_or_dash(link.get('type'))} | "
            f"{value_or_dash(link.get('issue_key'))} | "
            f"{value_or_dash(link.get('status'))} | "
            f"{value_or_dash(link.get('summary'))} |"
        )

    return "\n".join(lines) + "\n"


# Funcion para armar la tabla de subtareas
def render_subtasks(subtasks):
    if not subtasks:
        return "No hay subtareas registradas.\n"

    lines = []
    lines.append("| Tarjeta | Estado | Resumen |")
    lines.append("|---|---|---|")

    for subtask in subtasks:
        lines.append(
            f"| {value_or_dash(subtask.get('issue_key'))} | "
            f"{value_or_dash(subtask.get('status'))} | "
            f"{value_or_dash(subtask.get('summary'))} |"
        )

    return "\n".join(lines) + "\n"


# Funcion para mostrar el historial completo o solo los ultimos cambios si se pasa un limite
def render_history(history, limit=None):
    if not history:
        return "No hay historial registrado.\n"

    items = history

    if limit:
        items = history[-limit:]

    lines = []
    lines.append("| Fecha | Autor | Campo | Desde | Hacia |")
    lines.append("|---|---|---|---|---|")

    for item in items:
        lines.append(
            f"| {value_or_dash(item.get('created_at'))} | "
            f"{value_or_dash(item.get('author'))} | "
            f"{value_or_dash(item.get('field'))} | "
            f"{value_or_dash(item.get('from'))} | "
            f"{value_or_dash(item.get('to'))} |"
        )

    return "\n".join(lines) + "\n"


# Funcion para generar un resumen simple para IA, por ahora sin usar ningun modelo
def generate_ai_summary(issue):
    """
    Este resumen todavía NO usa IA.
    Es un resumen estructurado simple para que después sirva como base de chunks.
    """
    issue_key = value_or_dash(issue.get("issue_key"))
    title = value_or_dash(issue.get("title"))
    status = value_or_dash(issue.get("status"))
    sprint = value_or_dash(issue.get("sprint"))
    glpi_ticket = value_or_dash(issue.get("glpi_ticket"))
    assignee = value_or_dash(issue.get("assignee"))
    reporter = value_or_dash(issue.get("reporter"))
    resolved_by = value_or_dash(issue.get("resolved_by_inferred"))
    description = value_or_dash(issue.get("description"))

    return f"""La tarjeta {issue_key} corresponde a "{title}". 
Estado actual: {status}. 
Sprint: {sprint}. 
Ticket GLPI asociado: {glpi_ticket}. 
Solicitante/reporter: {reporter}. 
Responsable asignado: {assignee}. 
Resolutor inferido por historial: {resolved_by}. 
Descripción: {description}
"""


#Funcion de generacion del md
def generate_markdown(issue):
    issue_key = value_or_dash(issue.get("issue_key"))
    title = value_or_dash(issue.get("title"))

    md = f"""# {issue_key} - {title}

## 1. Datos generales

| Campo | Valor |
|---|---|
| Tarjeta | {issue_key} |
| Título | {title} |
| Tipo | {value_or_dash(issue.get("issue_type"))} |
| Estado | {value_or_dash(issue.get("status"))} |
| Prioridad | {value_or_dash(issue.get("priority"))} |
| Sprint | {value_or_dash(issue.get("sprint"))} |
| Ticket GLPI | {value_or_dash(issue.get("glpi_ticket"))} |
| Área de enfoque | {value_or_dash(issue.get("focus_area"))} |
| Responsable actual | {value_or_dash(issue.get("assignee"))} |
| Solicitante / Reporter | {value_or_dash(issue.get("reporter"))} |
| Creador | {value_or_dash(issue.get("creator"))} |
| Resolutor inferido | {value_or_dash(issue.get("resolved_by_inferred"))} |
| Fecha creación | {value_or_dash(issue.get("created_at"))} |
| Fecha actualización | {value_or_dash(issue.get("updated_at"))} |
| Fecha resolución | {value_or_dash(issue.get("resolved_at"))} |
| Link Jira | {value_or_dash(issue.get("jira_url"))} |

## 2. Descripción original

{safe_text(issue.get("description"))}

## 3. Clasificación

| Campo | Valor |
|---|---|
| Labels | {list_or_dash(issue.get("labels"))} |
| Componentes | {list_or_dash(issue.get("components"))} |

## 4. Comentarios

{render_comments(issue.get("comments"))}

## 5. Adjuntos / imágenes

{render_attachments(issue.get("attachments"))}

## 6. Subtareas

{render_subtasks(issue.get("subtasks"))}

## 7. Tarjetas relacionadas

{render_issue_links(issue.get("issue_links"))}

## 8. Historial de cambios

{render_history(issue.get("history"))}

## 9. Resumen estructurado para IA

{generate_ai_summary(issue)}

## 10. Fuente

- Archivo raw: `{value_or_dash(issue.get("raw_file"))}`
- Jira: {value_or_dash(issue.get("jira_url"))}
"""

    return md


# Funcion principal que recorre los json normalizados y genera un md por cada tarjeta
def main():
    normalized_files = list(NORMALIZED_DIR.glob("*.json"))

    if not normalized_files:
        print("No hay archivos normalizados para generar Markdown.")
        return

    for normalized_file in normalized_files:
        with open(normalized_file, "r", encoding="utf-8") as f:
            issue = json.load(f)

        issue_key = issue.get("issue_key")
        markdown = generate_markdown(issue)

        output_file = MARKDOWN_DIR / f"{issue_key}.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"Markdown generado {issue_key}: {output_file}")

    print("\nGeneración Markdown finalizada.")


if __name__ == "__main__":
    main()
