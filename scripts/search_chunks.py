# Buscador local para probar los chunks antes de sumar embeddings o una base vectorial

import argparse
import json
import re
from pathlib import Path


# Directorio donde generate_chunks.py deja los archivos listos para buscar
BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_DIR = BASE_DIR / "data" / "chunks"


# Pasamos todo a minusculas y sacamos acentos para comparar palabras de una forma mas pareja
def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()

    # Normalización simple de acentos comunes
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


# Separamos la consulta en palabras utiles y descartamos las que no aportan mucho
def tokenize(query):
    normalized = normalize_text(query)

    words = re.findall(r"\b\w+\b", normalized)

    # Estas palabras aparecen mucho pero no ayudan a distinguir una tarjeta de otra
    stopwords = {
        "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
        "y", "o", "en", "con", "por", "para", "que", "se", "del",
        "al", "a", "lo", "sobre", "como", "cual", "cuales", "que",
        "me", "mi", "su", "sus", "es", "son", "fue", "fueron",
        "tarjeta", "tarjetas"
    }

    return [word for word in words if word not in stopwords and len(word) > 2]


# Juntamos en memoria los chunks de todas las tarjetas para recorrerlos en una sola busqueda
def load_all_chunks():
    chunks = []

    if not CHUNKS_DIR.exists():
        return chunks

    for chunk_file in CHUNKS_DIR.glob("*.json"):
        # Cada archivo contiene la lista completa de chunks de una tarjeta
        with open(chunk_file, "r", encoding="utf-8") as f:
            issue_chunks = json.load(f)

        for chunk in issue_chunks:
            chunks.append(chunk)

    return chunks


# Calculamos un score simple: pesa mas el texto, suma metadata y da bonus a identificadores importantes
def calculate_score(chunk, query_terms):
    text = normalize_text(chunk.get("text", ""))
    metadata = chunk.get("metadata") or {}

    searchable_metadata = normalize_text(
        " ".join(
            str(value)
            for value in metadata.values()
            if value is not None
        )
    )

    score = 0
    matched_terms = []

    for term in query_terms:
        text_count = text.count(term)
        metadata_count = searchable_metadata.count(term)

        if text_count > 0 or metadata_count > 0:
            matched_terms.append(term)

        # El texto es lo principal porque ahi esta el contenido real de la tarjeta
        score += text_count * 3

        # La metadata ayuda a encontrar estados, sprints, responsables y otros datos puntuales
        score += metadata_count * 2

        # El titulo suele resumir muy bien la tarjeta, por eso tiene un bonus extra
        title = normalize_text(metadata.get("title"))
        if term in title:
            score += 5

        # Si buscaron una key o GLPI concreto queremos que aparezca bien arriba
        issue_key = normalize_text(metadata.get("issue_key"))
        glpi_ticket = normalize_text(metadata.get("glpi_ticket"))

        if term in issue_key:
            score += 10

        if term in glpi_ticket:
            score += 10

    return score, matched_terms


# Aplicamos filtros exactos antes del score para buscar sobre un conjunto mas chico
def apply_filters(chunks, status=None, sprint=None, issue_key=None, chunk_type=None):
    filtered = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}

        # Los filtros comparan valores completos, no coincidencias parciales
        if status:
            if normalize_text(metadata.get("status")) != normalize_text(status):
                continue

        if sprint:
            if normalize_text(metadata.get("sprint")) != normalize_text(sprint):
                continue

        if issue_key:
            if normalize_text(metadata.get("issue_key")) != normalize_text(issue_key):
                continue

        if chunk_type:
            if normalize_text(chunk.get("chunk_type")) != normalize_text(chunk_type):
                continue

        filtered.append(chunk)

    return filtered


# Acortamos el texto solamente al mostrarlo; el score usa siempre el chunk completo
def shorten(text, max_length=500):
    if not text:
        return ""

    clean = " ".join(str(text).split())

    if len(clean) <= max_length:
        return clean

    return clean[:max_length] + "..."


# Ejecutamos la busqueda completa: carga, filtros, ranking y muestra de resultados
def search(query, limit=10, status=None, sprint=None, issue_key=None, chunk_type=None):
    chunks = load_all_chunks()

    if not chunks:
        print("No hay chunks generados. Ejecutá primero scripts/generate_chunks.py")
        return

    chunks = apply_filters(
        chunks,
        status=status,
        sprint=sprint,
        issue_key=issue_key,
        chunk_type=chunk_type
    )

    query_terms = tokenize(query)

    # Si despues de sacar stopwords no queda nada, no hay una busqueda util para hacer
    if not query_terms:
        print("La búsqueda no tiene términos relevantes.")
        return

    # Guardamos solamente chunks con alguna coincidencia para no mostrar resultados sin relacion
    results = []

    for chunk in chunks:
        score, matched_terms = calculate_score(chunk, query_terms)

        if score > 0:
            results.append({
                "score": score,
                "matched_terms": matched_terms,
                "chunk": chunk,
            })

    # Ordenamos de mayor a menor para mostrar primero las coincidencias mas fuertes
    results.sort(key=lambda item: item["score"], reverse=True)

    print("\n" + "=" * 100)
    print(f"Búsqueda: {query}")
    print(f"Términos usados: {', '.join(query_terms)}")
    print(f"Resultados encontrados: {len(results)}")
    print("=" * 100)

    for index, result in enumerate(results[:limit], start=1):
        chunk = result["chunk"]
        metadata = chunk.get("metadata") or {}

        print(f"\n#{index} | Score: {result['score']}")
        print(f"Tarjeta: {metadata.get('issue_key')}")
        print(f"Título: {metadata.get('title')}")
        print(f"Tipo chunk: {chunk.get('chunk_type')}")
        print(f"Estado: {metadata.get('status')}")
        print(f"Sprint: {metadata.get('sprint')}")
        print(f"GLPI: {metadata.get('glpi_ticket')}")
        print(f"Jira: {metadata.get('jira_url')}")
        print(f"Términos encontrados: {', '.join(result['matched_terms'])}")
        print("-" * 100)
        print(shorten(chunk.get("text"), max_length=700))


# Leemos la consulta y los filtros opcionales desde la terminal
def main():
    parser = argparse.ArgumentParser(description="Buscador local simple sobre chunks de RAG Porta")

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

    search(
        query=args.query,
        limit=args.limit,
        status=args.status,
        sprint=args.sprint,
        issue_key=args.issue_key,
        chunk_type=args.chunk_type
    )


if __name__ == "__main__":
    main()
