import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

CHUNKS_DIR = BASE_DIR / "data" / "chunks"
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"

EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

EMBEDDINGS_FILE = EMBEDDINGS_DIR / "chunk_embeddings.npy"
CHUNKS_INDEX_FILE = EMBEDDINGS_DIR / "chunks_index.json"


def load_all_chunks():
    chunks = []

    if not CHUNKS_DIR.exists():
        return chunks

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        with open(chunk_file, "r", encoding="utf-8") as f:
            issue_chunks = json.load(f)

        for chunk in issue_chunks:
            text = chunk.get("text")

            if text and text.strip():
                chunks.append(chunk)

    return chunks


def main():
    print("Cargando chunks...")

    chunks = load_all_chunks()

    if not chunks:
        print("No hay chunks disponibles. Ejecutá primero scripts/generate_chunks.py")
        return

    print(f"Chunks cargados: {len(chunks)}")
    print(f"Cargando modelo: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    print("Generando embeddings...")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    np.save(EMBEDDINGS_FILE, embeddings)

    with open(CHUNKS_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print("\nEmbeddings generados correctamente.")
    print(f"Embeddings: {EMBEDDINGS_FILE}")
    print(f"Índice chunks: {CHUNKS_INDEX_FILE}")
    print(f"Shape embeddings: {embeddings.shape}")


if __name__ == "__main__":
    main()