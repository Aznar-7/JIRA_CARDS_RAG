# Este script corre todo el proceso de punta a punta:
# 1. Sincroniza Jira
# 2. Detecta tarjetas nuevas o modificadas
# 3. Normaliza solamente lo que cambio
# 4. Genera los Markdown que haga falta

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Directorios donde estan los scripts, los estados de sync y los logs de cada corrida
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "data" / "logs"
SYNC_DIR = BASE_DIR / "data" / "sync"

LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Fecha legible para guardar cuando arranco y termino cada paso
def now_iso():
    return datetime.now().isoformat(timespec="seconds")


# Armamos un id distinto por corrida para no pisar los logs anteriores
def build_run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# Leemos un JSON y devolvemos el valor por defecto si todavia no existe
def read_json_file(path, default=None):
    if default is None:
        default = None

    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Guardamos los logs y resumenes con formato facil de leer
def write_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Argparse confunde valores como -1d con opciones nuevas, asi que los pegamos a --since antes de parsear
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


# Ejecutamos un paso, mostramos su salida y devolvemos toda la info necesaria para el log
def run_step(command, step_name):
    print("\n" + "=" * 80)
    print(f"Ejecutando paso: {step_name}")
    print("=" * 80)

    started_at = now_iso()

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        capture_output=True
    )

    finished_at = now_iso()

    # Aunque capturemos la salida para el log, tambien la mostramos en consola
    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    step_log = {
        "name": step_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": "success" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

    if result.returncode != 0:
        print(f"\nError en paso: {step_name}")
        print(f"Código de salida: {result.returncode}")

    return step_log


# Armamos los comandos y frenamos el pipeline apenas falla alguno de los pasos
def main():
    parser = argparse.ArgumentParser(description="Pipeline completo read-only de Jira para RAG Porta")

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
        help="Cantidad máxima de tarjetas a traer desde Jira"
    )

    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help='Fecha manual para incremental. Ej: "2026-06-01" o "-1d"'
    )

    args = parser.parse_args(normalize_since_argument(sys.argv[1:]))

    run_id = build_run_id()
    started_at = now_iso()

    # El log se va actualizando despues de cada paso, asi queda algo util incluso si falla a mitad
    pipeline_log = {
        "run_id": run_id,
        "mode": args.mode,
        "max_results": args.max_results,
        "since": args.since,
        "started_at": started_at,
        "finished_at": None,
        "status": "running",
        "steps": [],
        "summary": {
            "changed_issues_count": None,
            "changed_issues": [],
        }
    }

    log_file = LOGS_DIR / f"pipeline_{run_id}.json"

    python_executable = sys.executable

    # Primero armamos el comando de sync con los argumentos que llegaron al pipeline
    sync_command = [
        python_executable,
        str(SCRIPTS_DIR / "jira" / "sync.py"),
        "--mode",
        args.mode,
        "--max-results",
        str(args.max_results),
    ]

    if args.since:
        sync_command.extend(["--since", args.since])

    # El orden importa porque cada paso usa los archivos que genero el anterior
    steps = [
        {
            "name": "Sincronización Jira",
            "command": sync_command,
        },
        {
            "name": "Detección de tarjetas nuevas o modificadas",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "transform" / "detect_changes.py")
            ],
        },
        {
            "name": "Normalización de tarjetas",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "transform" / "normalize.py")
            ],
        },
        {
            "name": "Generación de Markdown",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "transform" / "generate_markdown.py")
            ],
        },
        {
            "name": "Generación de chunks RAG",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "transform" / "generate_chunks.py")
    ],
},
    ]

    try:
        for step in steps:
            step_log = run_step(step["command"], step["name"])
            pipeline_log["steps"].append(step_log)

            write_json_file(log_file, pipeline_log)

            # Si un paso falla no seguimos, porque los resultados siguientes quedarian inconsistentes
            if step_log["status"] == "error":
                pipeline_log["status"] = "error"
                pipeline_log["finished_at"] = now_iso()
                write_json_file(log_file, pipeline_log)
                sys.exit(step_log["returncode"])

        # Sumamos al log final la lista de tarjetas que realmente se procesaron
        changed_file = SYNC_DIR / "changed_issues.json"
        changed_issues = read_json_file(changed_file, default=[])

        pipeline_log["summary"]["changed_issues"] = changed_issues
        pipeline_log["summary"]["changed_issues_count"] = len(changed_issues)

        pipeline_log["status"] = "success"
        pipeline_log["finished_at"] = now_iso()

        write_json_file(log_file, pipeline_log)

        print("\n" + "=" * 80)
        print("Pipeline completo finalizado correctamente.")
        print(f"Log generado: {log_file}")
        print("=" * 80)

    except Exception as error:
        # Tambien dejamos registrado cualquier error inesperado del propio pipeline
        pipeline_log["status"] = "error"
        pipeline_log["finished_at"] = now_iso()
        pipeline_log["error"] = str(error)

        write_json_file(log_file, pipeline_log)

        raise


if __name__ == "__main__":
    main()
