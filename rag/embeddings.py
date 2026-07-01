# rag/embeddings.py
import threading

import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str], show_progress: bool = False) -> np.ndarray:
    """Returns normalized embeddings, shape (len(texts), embedding_dim)."""
    model = _get_model()
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )


def embed_text(text: str) -> np.ndarray:
    """Returns a single normalized embedding vector."""
    return embed_texts([text])[0]
