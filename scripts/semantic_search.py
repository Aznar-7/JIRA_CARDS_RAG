import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

EMBEDDINGS_FILE = EMBEDDINGS_DIR / "chunk_embeddings.npy"
CHUNKS_INDEX_FILE = EMBEDDINGS_DIR / "chunks_index.json"


def load_index():
    if not EMBEDDINGS_FILE.exists() or not CHUNKS_INDEX_FILE.exists():
        raise FileNotFoundError(
            "No existe índice de embeddings. Ejecutá primero scripts/build_embeddings.py"
        )

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(CHUNKS_INDEX_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return embeddings, chunks


def shorten(text, max_length=700):
    if not text:
        return ""

    clean = " ".join(str(text).split())

    if len(clean) <= max_length:
        return clean

    return clean[:max_length] + "..."


def apply_filters(chunks, indexes, status=None, sprint=None, issue_key=None, chunk_type=None):
    filtered_indexes = []

    for idx in indexes:
        chunk = chunks[idx]
        metadata = chunk.get("metadata") or {}

        if status and str(metadata.get("status", "")).lower() != status.lower():
            continue

        if sprint and str(metadata.get("sprint", "")).lower() != sprint.lower():
            continue

        if issue_key and str(metadata.get("issue_key", "")).lower() != issue_key.lower():
            continue

        if chunk_type and str(chunk.get("chunk_type", "")).lower() != chunk_type.lower():
            continue

        filtered_indexes.append(idx)

    return filtered_indexes


def semantic_search(query, limit=10, status=None, sprint=None, issue_key=None, chunk_type=None):
    print("Cargando índice...")
    embeddings, chunks = load_index()

    print(f"Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    all_indexes = list(range(len(chunks)))

    candidate_indexes = apply_filters(
        chunks=chunks,
        indexes=all_indexes,
        status=status,
        sprint=sprint,
        issue_key=issue_key,
        chunk_type=chunk_type
    )

    if not candidate_indexes:
        print("No hay chunks que coincidan con los filtros.")
        return

    candidate_embeddings = embeddings[candidate_indexes]

    # Como los embeddings están normalizados, el dot product equivale a similitud coseno.
    similarities = candidate_embeddings @ query_embedding

    ranked_positions = np.argsort(similarities)[::-1]

    print("\n" + "=" * 100)
    print(f"Búsqueda semántica: {query}")
    print(f"Resultados candidatos: {len(candidate_indexes)}")
    print("=" * 100)

    for rank, pos in enumerate(ranked_positions[:limit], start=1):
        original_index = candidate_indexes[pos]
        chunk = chunks[original_index]
        metadata = chunk.get("metadata") or {}
        similarity = float(similarities[pos])

        print(f"\n#{rank} | Similaridad: {similarity:.4f}")
        print(f"Tarjeta: {metadata.get('issue_key')}")
        print(f"Título: {metadata.get('title')}")
        print(f"Tipo chunk: {chunk.get('chunk_type')}")
        print(f"Estado: {metadata.get('status')}")
        print(f"Sprint: {metadata.get('sprint')}")
        print(f"GLPI: {metadata.get('glpi_ticket')}")
        print(f"Jira: {metadata.get('jira_url')}")
        print("-" * 100)
        print(shorten(chunk.get("text"), max_length=700))


def main():
    parser = argparse.ArgumentParser(description="Buscador semántico local sobre chunks de RAG Porta")

    parser.add_argument(
        "query",
        type=str,
        help="Texto a buscar"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Cantidad máxima de resultados"
    )

    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filtrar por estado exacto. Ej: Finalizada"
    )

    parser.add_argument(
        "--sprint",
        type=str,
        default=None,
        help="Filtrar por sprint exacto. Ej: MAY-26B"
    )

    parser.add_argument(
        "--issue-key",
        type=str,
        default=None,
        help="Filtrar por tarjeta exacta. Ej: PE20-1034"
    )

    parser.add_argument(
        "--chunk-type",
        type=str,
        default=None,
        help="Filtrar por tipo de chunk. Ej: description, history, attachments"
    )

    args = parser.parse_args()

    semantic_search(
        query=args.query,
        limit=args.limit,
        status=args.status,
        sprint=args.sprint,
        issue_key=args.issue_key,
        chunk_type=args.chunk_type
    )


if __name__ == "__main__":
    main()