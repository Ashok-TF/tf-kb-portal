from __future__ import annotations

from app.config import Settings


def generate_answer(settings: Settings, query: str, context_chunks: list[str]) -> str:
    if not context_chunks:
        return "I could not find relevant information in the knowledge base to answer that question."

    context = "\n\n---\n\n".join(context_chunks[:8])

    if settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful enterprise knowledge base assistant. "
                            "Answer only using the provided context. If the answer is not in "
                            "the context, say you don't know. Be concise."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            return f"(LLM unavailable: {exc})\n\nBased on retrieved excerpts:\n{context_chunks[0][:500]}"

    # Offline fallback: summarize top chunk
    return (
        f"Based on the most relevant document excerpt:\n\n{context_chunks[0][:800]}"
        "\n\n(Enable OPENAI_API_KEY for full grounded answers.)"
    )
