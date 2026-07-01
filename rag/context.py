# rag/context.py
import anthropic

from core.config import settings

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def build_context(chunks: list[dict]) -> str:
    """Wraps each chunk in tagged blocks to prevent prompt injection."""
    parts = []
    for chunk in chunks:
        parts.append(
            f'<ticket id="{chunk["chunk_id"]}">\n{chunk["text"]}\n</ticket>'
        )
    return "\n\n".join(parts)


async def condense_question(question: str, history: list[dict]) -> str:
    """Rewrites a follow-up question as a standalone query using conversation history.
    Returns the original question unchanged when there is no history."""
    if not history:
        return question

    client = _get_client()

    history_text = "\n".join(
        f"{m['role']}: {m['content'][:300]}" for m in history[-4:]
    )

    response = await client.messages.create(
        model=settings.condensation_model,
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Conversation so far:\n{history_text}\n\n"
                    f'Rewrite this follow-up question as a standalone question:\n"{question}"\n\n'
                    "Return ONLY the rewritten question, nothing else."
                ),
            }
        ],
    )
    return response.content[0].text.strip()
