import argparse
import json
import os
import sys
from datetime import datetime, timezone
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

# Config de directorios para guardar los json raw y el estado del ultimo sync
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
SYNC_DIR = BASE_DIR / "data" / "sync"
SYNC_STATE_FILE = SYNC_DIR / "sync_state.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
SYNC_DIR.mkdir(parents=True, exist_ok=True)

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


# Funcion para obtener la fecha y hora actual en UTC
def now_iso():
    return datetime.now(timezone.utc).isoformat()


# Funcion para leer el estado del ultimo sync o devolver uno vacio si todavia no existe
def load_sync_state():
    if not SYNC_STATE_FILE.exists():
        return {
            "last_successful_sync": None,
            "last_mode": None,
            "last_issue_count": 0
        }

    with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Funcion para guardar cuando termino el sync, el modo usado y cuantas tarjetas encontro
def save_sync_state(mode, issue_count):
    state = {
        "last_successful_sync": now_iso(),
        "last_mode": mode,
        "last_issue_count": issue_count
    }

    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"\nEstado de sync guardado en: {SYNC_STATE_FILE}")


# Funcion para armar el JQL segun sea un sync completo o incremental
def build_jql(mode, since=None):
    if mode == "full":
        return f'project = "{JIRA_PROJECT_KEY}" ORDER BY updated DESC'

    if mode == "incremental":
        if not since:
            raise ValueError("Para modo incremental se necesita una fecha since.")

        return f'project = "{JIRA_PROJECT_KEY}" AND updated >= "{since}" ORDER BY updated DESC'

    raise ValueError(f"Modo inválido: {mode}")


# Funcion para buscar las tarjetas que coinciden con el JQL y devolver sus keys
def search_issue_keys(jql, max_results):
    print("\n1) Buscando tarjetas...")

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "key"
    }

    data = jira_get("/rest/api/3/search/jql", params=params)

    issues = data.get("issues", [])
    issue_keys = [issue.get("key") for issue in issues if issue.get("key")]

    print(f"\nTarjetas encontradas: {len(issue_keys)}")

    for key in issue_keys:
        print(f"- {key}")

    return issue_keys


# Funcion para traer todos los datos de una tarjeta y guardarlos como json raw
def fetch_full_issue(issue_key):
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

    return issue


# Funcion para ejecutar el sync completo de las tarjetas del proyecto
def run_full_sync(max_results):
    print("\n=== FULL SYNC ===")

    jql = build_jql(mode="full")
    print(f"JQL: {jql}")

    issue_keys = search_issue_keys(jql, max_results=max_results)

    for issue_key in issue_keys:
        fetch_full_issue(issue_key)

    save_sync_state(mode="full", issue_count=len(issue_keys))

    print("\nFull sync finalizado.")


# Funcion para convertir la fecha guardada a un formato que Jira entienda en el JQL
def format_jira_datetime_from_iso(iso_value):
    """
    Convierte una fecha ISO UTC del sync_state a formato usable en JQL.

    Ejemplo:
    2026-06-10T13:20:00.000000+00:00
    ->
    2026-06-10 13:20
    """
    dt = datetime.fromisoformat(iso_value)
    return dt.strftime("%Y-%m-%d %H:%M")


# Funcion para traer solo las tarjetas actualizadas desde el ultimo sync o una fecha manual
def run_incremental_sync(max_results, since_override=None):
    print("\n=== INCREMENTAL SYNC ===")

    state = load_sync_state()

    if since_override:
        since = since_override
    else:
        last_sync = state.get("last_successful_sync")

        if not last_sync:
            print("No existe last_successful_sync. Ejecutando incremental de últimas 24h como fallback.")
            since = "-1d"
        else:
            since = format_jira_datetime_from_iso(last_sync)

    jql = build_jql(mode="incremental", since=since)
    print(f"JQL: {jql}")

    issue_keys = search_issue_keys(jql, max_results=max_results)

    for issue_key in issue_keys:
        fetch_full_issue(issue_key)

    save_sync_state(mode="incremental", issue_count=len(issue_keys))

    print("\nIncremental sync finalizado.")


# Funcion para revisar que no falte ninguna variable necesaria en el .env
def validate_env():
    missing = []

    values = {
        "JIRA_BASE_URL": JIRA_BASE_URL,
        "JIRA_EMAIL": JIRA_EMAIL,
        "JIRA_API_TOKEN": JIRA_API_TOKEN,
        "JIRA_PROJECT_KEY": JIRA_PROJECT_KEY,
    }

    for key, value in values.items():
        if not value:
            missing.append(key)

    if missing:
        raise ValueError(f"Faltan variables en .env: {', '.join(missing)}")


# Argparse toma valores como -1d como si fueran otra opcion, asi que los pegamos a --since
def normalize_since_argument(arguments):
    normalized = []
    index = 0

    while index < len(arguments):
        argument = arguments[index]

        if (
            argument == "--since"
            and index + 1 < len(arguments)
            and not arguments[index + 1].startswith("--")
        ):
            normalized.append(f"--since={arguments[index + 1]}")
            index += 2
            continue

        normalized.append(argument)
        index += 1

    return normalized


# Funcion principal que lee los argumentos y ejecuta el modo de sync elegido
def main():
    validate_env()

    parser = argparse.ArgumentParser(description="Sincronizador read-only de Jira para RAG Porta")

    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        required=True,
        help="Modo de sincronización"
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Cantidad máxima de tarjetas a traer"
    )

    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help='Fecha manual para incremental. Ej: "2026-06-01" o "-1d"'
    )

    args = parser.parse_args(normalize_since_argument(sys.argv[1:]))

    if args.mode == "full":
        run_full_sync(max_results=args.max_results)

    if args.mode == "incremental":
        run_incremental_sync(
            max_results=args.max_results,
            since_override=args.since
        )


if __name__ == "__main__":
    main()
