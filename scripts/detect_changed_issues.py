import hashlib
import json
from pathlib import Path


# Directorios que usa este paso para leer los raw y guardar el resultado
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
HASH_DIR = BASE_DIR / "data" / "hashes"
SYNC_DIR = BASE_DIR / "data" / "sync"

HASH_FILE = HASH_DIR / "raw_hashes.json"
CHANGED_FILE = SYNC_DIR / "changed_issues.json"

HASH_DIR.mkdir(parents=True, exist_ok=True)
SYNC_DIR.mkdir(parents=True, exist_ok=True)


# Calculamos un hash del archivo completo para saber si cambio sin comparar el JSON campo por campo
def calculate_file_hash(file_path):
    """
    El hash funciona como una huella del archivo.
    Si cambia cualquier cosa del JSON raw, esta huella tambien cambia.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# Levantamos los hashes de la corrida anterior; si es la primera vez arrancamos con un diccionario vacio
def load_previous_hashes():
    if not HASH_FILE.exists():
        return {}

    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Guardamos los hashes actuales para poder compararlos en la proxima corrida
def save_hashes(hashes):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


# Dejamos una lista simple de tarjetas modificadas para que los pasos siguientes procesen solo esas
def save_changed_issues(changed_issues):
    with open(CHANGED_FILE, "w", encoding="utf-8") as f:
        json.dump(changed_issues, f, ensure_ascii=False, indent=2)


# Recorremos todos los raw, comparamos los hashes y armamos la lista de lo que cambio
def main():
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    changed_issues = []

    raw_files = list(RAW_DIR.glob("*.json"))

    if not raw_files:
        print("No hay archivos raw para analizar.")
        return

    for raw_file in raw_files:
        # El nombre del archivo ya es la key de Jira, por ejemplo PORTA-123.json
        issue_key = raw_file.stem
        current_hash = calculate_file_hash(raw_file)

        current_hashes[issue_key] = current_hash

        previous_hash = previous_hashes.get(issue_key)

        # Tambien entra aca una tarjeta nueva, porque todavia no tiene hash anterior
        if previous_hash != current_hash:
            changed_issues.append(issue_key)

    # Reemplazamos el estado completo para no guardar hashes de raw que ya no existen
    save_hashes(current_hashes)
    save_changed_issues(changed_issues)

    print(f"Archivos raw analizados: {len(raw_files)}")
    print(f"Tarjetas nuevas o modificadas: {len(changed_issues)}")

    for issue_key in changed_issues:
        print(f"- {issue_key}")

    print(f"\nListado guardado en: {CHANGED_FILE}")


if __name__ == "__main__":
    main()
