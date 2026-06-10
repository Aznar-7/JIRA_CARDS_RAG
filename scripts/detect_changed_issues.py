import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
HASH_DIR = BASE_DIR / "data" / "hashes"
SYNC_DIR = BASE_DIR / "data" / "sync"

HASH_FILE = HASH_DIR / "raw_hashes.json"
CHANGED_FILE = SYNC_DIR / "changed_issues.json"

HASH_DIR.mkdir(parents=True, exist_ok=True)
SYNC_DIR.mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_path):
    """
    Calcula hash SHA256 del archivo.
    Si cambia cualquier contenido del JSON raw, cambia el hash.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_previous_hashes():
    if not HASH_FILE.exists():
        return {}

    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_hashes(hashes):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def save_changed_issues(changed_issues):
    with open(CHANGED_FILE, "w", encoding="utf-8") as f:
        json.dump(changed_issues, f, ensure_ascii=False, indent=2)


def main():
    previous_hashes = load_previous_hashes()
    current_hashes = {}
    changed_issues = []

    raw_files = list(RAW_DIR.glob("*.json"))

    if not raw_files:
        print("No hay archivos raw para analizar.")
        return

    for raw_file in raw_files:
        issue_key = raw_file.stem
        current_hash = calculate_file_hash(raw_file)

        current_hashes[issue_key] = current_hash

        previous_hash = previous_hashes.get(issue_key)

        if previous_hash != current_hash:
            changed_issues.append(issue_key)

    save_hashes(current_hashes)
    save_changed_issues(changed_issues)

    print(f"Archivos raw analizados: {len(raw_files)}")
    print(f"Tarjetas nuevas o modificadas: {len(changed_issues)}")

    for issue_key in changed_issues:
        print(f"- {issue_key}")

    print(f"\nListado guardado en: {CHANGED_FILE}")


if __name__ == "__main__":
    main()