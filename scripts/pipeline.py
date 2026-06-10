# Esta cosita magica va a hacer:
#1. Sincronizar Jira
#2. Detectar tarjetas nuevas/modificadas
#3. Normalizar solo modificadas
#4. Generar Markdown solo de modificadas

import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"


def run_step(command, step_name):
    print("\n" + "=" * 80)
    print(f"Ejecutando paso: {step_name}")
    print("=" * 80)

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True
    )

    if result.returncode != 0:
        print(f"\nError en paso: {step_name}")
        print(f"Código de salida: {result.returncode}")
        sys.exit(result.returncode)

    print(f"\nPaso finalizado correctamente: {step_name}")


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

    run_step(
        sync_command,
        "Sincronización Jira"
    )

    run_step(
        [
            python_executable,
            str(SCRIPTS_DIR / "detect_changed_issues.py")
        ],
        "Detección de tarjetas nuevas o modificadas"
    )

    run_step(
        [
            python_executable,
            str(SCRIPTS_DIR / "normalize_issues.py")
        ],
        "Normalización de tarjetas"
    )

    run_step(
        [
            python_executable,
            str(SCRIPTS_DIR / "generate_markdown.py")
        ],
        "Generación de Markdown"
    )

    print("\n" + "=" * 80)
    print("Pipeline completo finalizado correctamente.")
    print("=" * 80)


if __name__ == "__main__":
    main()