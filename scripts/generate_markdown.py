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


def list_or_dash(items):
    if not items:
        return "-"

    return ", ".join(str(item) for item in items)


#Funcion de generacion del md
def generate_markdown(issue):
    issue_key = value_or_dash(issue.get("issue_key"))
    title = value_or_dash(issue.get("title"))

    md = f"""# {issue_key} - {title}

## Datos generales

| Campo | Valor |
|---|---|
| Tarjeta | {issue_key} |
| Título | {title} |
| Tipo | {value_or_dash(issue.get("issue_type"))} |
| Estado | {value_or_dash(issue.get("status"))} |
| Prioridad | {value_or_dash(issue.get("priority"))} |
| Sprint | {value_or_dash(issue.get("sprint"))} |
| Ticket GLPI | {value_or_dash(issue.get("glpi_ticket"))} |
| Responsable | {value_or_dash(issue.get("assignee"))} |
| Solicitante / Reporter | {value_or_dash(issue.get("reporter"))} |
| Creador | {value_or_dash(issue.get("creator"))} |
| Fecha creación | {value_or_dash(issue.get("created_at"))} |
| Fecha actualización | {value_or_dash(issue.get("updated_at"))} |
| Fecha resolución | {value_or_dash(issue.get("resolved_at"))} |
| Link Jira | {value_or_dash(issue.get("jira_url"))} |

## Descripción original

{value_or_dash(issue.get("description"))}

## Clasificación

| Campo | Valor |
|---|---|
| Labels | {list_or_dash(issue.get("labels"))} |
| Componentes | {list_or_dash(issue.get("components"))} |

## Resumen para IA

Tarjeta {issue_key}: {title}.  
Estado: {value_or_dash(issue.get("status"))}.  
Sprint: {value_or_dash(issue.get("sprint"))}.  
Responsable: {value_or_dash(issue.get("assignee"))}.  
Solicitante: {value_or_dash(issue.get("reporter"))}.  
Descripción: {value_or_dash(issue.get("description"))}

## Fuente

- Archivo raw: `{value_or_dash(issue.get("raw_file"))}`
- Jira: {value_or_dash(issue.get("jira_url"))}
"""

    return md


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