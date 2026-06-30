# core/text.py
import re

_ACCENT_MAP = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "en", "con", "por", "para", "que", "se", "del",
    "al", "a", "lo", "sobre", "como", "cual", "cuales",
    "me", "mi", "su", "sus", "es", "son", "fue", "fueron",
    "tarjeta", "tarjetas",
}


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return str(text).lower().translate(_ACCENT_MAP)


def tokenize(query: str) -> list[str]:
    normalized = normalize_text(query)
    words = re.findall(r"\b\w+\b", normalized)
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]


def value_or_dash(value) -> str:
    if value is None or value == "" or value == []:
        return "-"
    return str(value)
