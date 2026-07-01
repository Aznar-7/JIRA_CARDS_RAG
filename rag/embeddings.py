# rag/embeddings.py
import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns normalized embeddings of shape (len(texts), 384)."""
    model = _get_model()
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )


def embed_text(text: str) -> np.ndarray:
    """Returns a single normalized embedding of shape (384,)."""
    return embed_texts([text])[0]
