# Esta cosita magica va a hacer:
#1. Sincronizar Jira
#2. Detectar tarjetas nuevas/modificadas
#3. Normalizar solo modificadas
#4. Generar Markdown solo de modificadas

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "data" / "logs"
SYNC_DIR = BASE_DIR / "data" / "sync"

LOGS_DIR.mkdir(parents=True, exist_ok=True)


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def build_run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json_file(path, default=None):
    if default is None:
        default = None

    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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

    # Mostramos salida en consola igual que antes
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

    args = parser.parse_args()

    run_id = build_run_id()
    started_at = now_iso()

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

    sync_command = [
        python_executable,
        str(SCRIPTS_DIR / "sync_jira.py"),
        "--mode",
        args.mode,
        "--max-results",
        str(args.max_results),
    ]

    if args.since:
        sync_command.extend(["--since", args.since])

    steps = [
        {
            "name": "Sincronización Jira",
            "command": sync_command,
        },
        {
            "name": "Detección de tarjetas nuevas o modificadas",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "detect_changed_issues.py")
            ],
        },
        {
            "name": "Normalización de tarjetas",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "normalize_issues.py")
            ],
        },
        {
            "name": "Generación de Markdown",
            "command": [
                python_executable,
                str(SCRIPTS_DIR / "generate_markdown.py")
            ],
        },
    ]

    try:
        for step in steps:
            step_log = run_step(step["command"], step["name"])
            pipeline_log["steps"].append(step_log)

            write_json_file(log_file, pipeline_log)

            if step_log["status"] == "error":
                pipeline_log["status"] = "error"
                pipeline_log["finished_at"] = now_iso()
                write_json_file(log_file, pipeline_log)
                sys.exit(step_log["returncode"])

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
        pipeline_log["status"] = "error"
        pipeline_log["finished_at"] = now_iso()
        pipeline_log["error"] = str(error)

        write_json_file(log_file, pipeline_log)

        raise


if __name__ == "__main__":
    main()