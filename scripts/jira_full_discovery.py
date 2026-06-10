import os
import json
from pathlib import Path
import urllib3

import requests
from dotenv import load_dotenv


# Carga de variables del .env para conectarse a Jira
load_dotenv()

# Se desactiva el warning porque por ahora usamos verify=False por el certificado corporativo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Config de Jira
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

# Config de directorios para guardar las respuestas completas de Jira
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Sesion reutilizable con la autenticacion y headers necesarios para Jira
session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
session.headers.update({
    "Accept": "application/json"
})


# Funcion generica para hacer consultas GET a Jira y controlar errores
def jira_get(path, params=None):
    """
    Wrapper read-only.
    Este script solo usa GET.
    """
    url = f"{JIRA_BASE_URL}{path}"

    response = session.get(
        url,
        params=params,
        timeout=60,
        verify=False  # Temporal por certificado corporativo
    )

    print(f"GET {response.url} -> {response.status_code}")

    if not response.ok:
        print(response.text)
        response.raise_for_status()

    return response.json()


# Funcion para buscar las tarjetas mas recientes del proyecto
def search_issue_keys(max_results=20):
    """
    Busca las tarjetas más recientes del proyecto y devuelve sus keys.
    """
    print("\n1) Buscando tarjetas recientes...")

    jql = f'project = "{JIRA_PROJECT_KEY}" ORDER BY updated DESC'

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "key"
    }

    data = jira_get("/rest/api/3/search/jql", params=params)

    issues = data.get("issues", [])
    issue_keys = [issue.get("key") for issue in issues if issue.get("key")]

    print(f"Tarjetas encontradas: {len(issue_keys)}")

    for key in issue_keys:
        print(f"- {key}")

    return issue_keys


# Funcion para traer todos los datos de una tarjeta y guardarlos como json raw
def fetch_full_issue(issue_key):
    """
    Obtiene detalle completo de una tarjeta.
    """
    print(f"\n2) Obteniendo detalle completo de {issue_key}...")

    params = {
        "fields": "*all",
        "expand": "changelog,renderedFields,names,schema"
    }

    issue = jira_get(f"/rest/api/3/issue/{issue_key}", params=params)

    output_file = RAW_DIR / f"{issue_key}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(issue, f, ensure_ascii=False, indent=2)

    print(f"Guardada {issue_key}: {output_file}")


# Funcion principal que valida el .env y ejecuta el discovery de las tarjetas
def main():
    if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        raise ValueError("Faltan variables en el .env")

    issue_keys = search_issue_keys(max_results=20)

    for issue_key in issue_keys:
        fetch_full_issue(issue_key)

    print("\nDiscovery completo finalizado.")


if __name__ == "__main__":
    main()
