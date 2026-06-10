import urllib3
import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


# Config de las v de entorno
JIRA_BASE_URL= os.getenv("JIRA_BASE_URL")
JIRA_EMAIL= os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN=os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY=os.getenv("JIRA_PROJECT_KEY")

# Config de directorios (se crean si no existen)
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR= BASE_DIR / "data" / "raw"
FIELDS_DIR= BASE_DIR / "data" / "fields"

RAW_DIR.mkdir(parents=True, exist_ok=True)
FIELDS_DIR.mkdir(parents=True, exist_ok=True)


# Config de la sesion de red
session = requests.Session() # Creo la sesion para reutilizar al conexion a las peticiones
session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
session.headers.update({
    "Accept": "application/json"
})

# Funciones para las consultas a la API de Jira aaaaaaaaa

# GET de consulta generica, con manejo de errores y logging básico
def jira_get(path, params=None):
    """
    Wrapper para asegurar que solo usamos GET.
    No existe lógica de POST, PUT ni DELETE en este script, para que no me caguen a pedos por romper el tablero.
    """
    url = f"{JIRA_BASE_URL}{path}"
    response = session.get(url, params=params, timeout=30, verify=False)

    print(f"GET {response.url} -> {response.status_code}")

    if not response.ok:
        print(response.text)
        response.raise_for_status() # Excepcion para parar la req si salio mal

    return response.json()

#Funcion para probar la conexion con jira y mostrar el usuario con el que se conecto
def test_connection():
    print("\n1) Probando conexión...")
    data = jira_get("/rest/api/3/myself")

    print("Conectado como:")
    print(data.get("displayName"))
    print(data.get("emailAddress"))

# Funcion para obtener los campos disponibles en el proyecto, guardarlos en un json, y mostrar los que podrían ser relevantes para la extracción de datos (con palabras clave)
def fetch_fields():
    print("\n2) Obteniendo campos disponibles...")
    fields = jira_get("/rest/api/3/field")

    output_file = FIELDS_DIR / "jira_fields.json"  # Guardo el json en el dir que cree antes y ademas guardo el nombre del archivo como "jira_fields.json" para que sea facil de identificar
    with open(output_file, "w", encoding="utf-8") as f: # Escribo la info en el archivo, en realidad primero abro el archivo con modo W (write)
        json.dump(fields, f, ensure_ascii=False, indent=2) # Aca si escribo la info en el archivo como json

    print(f"Campos guardados en: {output_file}")

    print("\nCampos que podrían interesar:")
    keywords = ["sprint", "glpi", "solicit", "resol", "modulo", "módulo", "area", "área"]
    for field in fields:
        name = field.get("name", "").lower()
        if any(k in name for k in keywords):
            print(f"- {field.get('id')} | {field.get('name')}")


# Funcion para getear las tarjetas recientes del proyecto, guardarlas como json en el dir de raw, y mostrar un resumen de las mismas (key, resumen, estado, fecha de actualizacion)
def fetch_recent_issues():
    print("\n3) Obteniendo tarjetas recientes...")

    jql = f'project = "{JIRA_PROJECT_KEY}" ORDER BY updated DESC'

    params = {
        "jql": jql,
        "maxResults": 10,
        "fields": "*all",
        "expand": "changelog"
    }

    data = jira_get("/rest/api/3/search/jql", params=params)

    issues = data.get("issues", [])

    print(f"Tarjetas encontradas: {len(issues)}")

    for issue in issues:
        key = issue.get("key")
        output_file = RAW_DIR / f"{key}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(issue, f, ensure_ascii=False, indent=2)

        print(f"- Guardada {key}: {output_file}")


# Punto de entrada del script (para que no se ejecute nada al importar, y solo corra si se ejecuta directamente) 
if __name__ == "__main__":
    if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        raise ValueError("Faltan variables en el .env")

    test_connection()
    fetch_fields()
    fetch_recent_issues()

    print("\nDiscovery finalizado.")