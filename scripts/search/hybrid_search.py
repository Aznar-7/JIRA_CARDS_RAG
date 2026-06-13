import argparse
import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent.parent

CHUNKS_DIR = BASE_DIR / "data" / "chunks"
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

EMBEDDINGS_FILE = EMBEDDINGS_DIR / "chunk_embeddings.npy"
CHUNKS_INDEX_FILE = EMBEDDINGS_DIR / "chunks_index.json"


def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    return text


def tokenize(query):
    normalized = normalize_text(query)

    words = re.findall(r"\b\w+\b", normalized)

    stopwords = {
        "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
        "y", "o", "en", "con", "por", "para", "que", "se", "del",
        "al", "a", "lo", "sobre", "como", "cual", "cuales",
        "me", "mi", "su", "sus", "es", "son", "fue", "fueron",
        "tarjeta", "tarjetas"
    }

    return [word for word in words if word not in stopwords and len(word) > 2]


def load_index():
    if not EMBEDDINGS_FILE.exists() or not CHUNKS_INDEX_FILE.exists():
        raise FileNotFoundError(
            "No existe índice de embeddings. Ejecutá primero: python scripts/build_embeddings.py"
        )

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(CHUNKS_INDEX_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return embeddings, chunks


def apply_filters(chunks, indexes, status=None, sprint=None, issue_key=None, chunk_type=None):
    filtered_indexes = []

    for idx in indexes:
        chunk = chunks[idx]
        metadata = chunk.get("metadata") or {}

        if status and normalize_text(metadata.get("status")) != normalize_text(status):
            continue

        if sprint and normalize_text(metadata.get("sprint")) != normalize_text(sprint):
            continue

        if issue_key and normalize_text(metadata.get("issue_key")) != normalize_text(issue_key):
            continue

        if chunk_type and normalize_text(chunk.get("chunk_type")) != normalize_text(chunk_type):
            continue

        filtered_indexes.append(idx)

    return filtered_indexes


def literal_score(chunk, query_terms):
    text = normalize_text(chunk.get("text", ""))
    metadata = chunk.get("metadata") or {}

    metadata_text = normalize_text(
        " ".join(str(value) for value in metadata.values() if value is not None)
    )

    title = normalize_text(metadata.get("title"))
    issue_key = normalize_text(metadata.get("issue_key"))
    glpi_ticket = normalize_text(metadata.get("glpi_ticket"))

    score = 0
    matched_terms = []

    for term in query_terms:
        text_count = text.count(term)
        metadata_count = metadata_text.count(term)

        if text_count > 0 or metadata_count > 0:
            matched_terms.append(term)

        score += text_count * 3
        score += metadata_count * 2

        if term in title:
            score += 5

        if term in issue_key:
            score += 15

        if term in glpi_ticket:
            score += 15

    return score, matched_terms


def normalize_scores(scores):
    scores = np.array(scores, dtype=float)

    if len(scores) == 0:
        return scores

    max_score = scores.max()
    min_score = scores.min()

    if max_score == min_score:
        if max_score == 0:
            return np.zeros_like(scores)
        return np.ones_like(scores)

    return (scores - min_score) / (max_score - min_score)


def shorten(text, max_length=700):
    if not text:
        return ""

    clean = " ".join(str(text).split())

    if len(clean) <= max_length:
        return clean

    return clean[:max_length] + "..."


def hybrid_search(
    query,
    limit=10,
    semantic_weight=0.65,
    literal_weight=0.35,
    status=None,
    sprint=None,
    issue_key=None,
    chunk_type=None,
):
    embeddings, chunks = load_index()

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

    query_terms = tokenize(query)

    candidate_embeddings = embeddings[candidate_indexes]

    semantic_scores = candidate_embeddings @ query_embedding

    literal_scores = []
    matched_terms_by_index = {}

    for idx in candidate_indexes:
        score, matched_terms = literal_score(chunks[idx], query_terms)
        literal_scores.append(score)
        matched_terms_by_index[idx] = matched_terms

    semantic_scores_norm = normalize_scores(semantic_scores)
    literal_scores_norm = normalize_scores(literal_scores)

    final_results = []

    for position, idx in enumerate(candidate_indexes):
        final_score = (
            semantic_scores_norm[position] * semantic_weight
            + literal_scores_norm[position] * literal_weight
        )

        final_results.append({
            "index": idx,
            "final_score": float(final_score),
            "semantic_score": float(semantic_scores[position]),
            "literal_score": float(literal_scores[position]),
            "matched_terms": matched_terms_by_index[idx],
        })

    final_results.sort(key=lambda item: item["final_score"], reverse=True)

    print("\n" + "=" * 100)
    print(f"Búsqueda híbrida: {query}")
    print(f"Pesos: semántico={semantic_weight}, literal={literal_weight}")
    print(f"Resultados candidatos: {len(candidate_indexes)}")
    print("=" * 100)

    for rank, result in enumerate(final_results[:limit], start=1):
        chunk = chunks[result["index"]]
        metadata = chunk.get("metadata") or {}

        print(f"\n#{rank} | Score final: {result['final_score']:.4f}")
        print(f"Score semántico: {result['semantic_score']:.4f}")
        print(f"Score literal: {result['literal_score']:.4f}")
        print(f"Tarjeta: {metadata.get('issue_key')}")
        print(f"Título: {metadata.get('title')}")
        print(f"Tipo chunk: {chunk.get('chunk_type')}")
        print(f"Estado: {metadata.get('status')}")
        print(f"Sprint: {metadata.get('sprint')}")
        print(f"GLPI: {metadata.get('glpi_ticket')}")
        print(f"Jira: {metadata.get('jira_url')}")

        if result["matched_terms"]:
            print(f"Términos literales encontrados: {', '.join(result['matched_terms'])}")
        else:
            print("Términos literales encontrados: -")

        print("-" * 100)
        print(shorten(chunk.get("text"), max_length=700))


def main():
    parser = argparse.ArgumentParser(description="Buscador híbrido local sobre chunks de RAG Porta")

    parser.add_argument("query", type=str, help="Texto a buscar")

    parser.add_argument("--limit", type=int, default=10)

    parser.add_argument("--semantic-weight", type=float, default=0.65)

    parser.add_argument("--literal-weight", type=float, default=0.35)

    parser.add_argument("--status", type=str, default=None)

    parser.add_argument("--sprint", type=str, default=None)

    parser.add_argument("--issue-key", type=str, default=None)

    parser.add_argument("--chunk-type", type=str, default=None)

    args = parser.parse_args()

    hybrid_search(
        query=args.query,
        limit=args.limit,
        semantic_weight=args.semantic_weight,
        literal_weight=args.literal_weight,
        status=args.status,
        sprint=args.sprint,
        issue_key=args.issue_key,
        chunk_type=args.chunk_type,
    )


if __name__ == "__main__":
    main()
