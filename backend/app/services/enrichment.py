from __future__ import annotations

import json

from app.config import Settings


def enrich_document(settings: Settings, text: str, filename: str) -> tuple[str | None, str | None]:
    """Return (summary, entities_json) or (None, None) on failure."""
    if not text.strip():
        return None, None

    excerpt = text[:4000]

    if not settings.openai_api_key:
        summary = excerpt[:400] + ("..." if len(excerpt) > 400 else "")
        return summary, json.dumps({"source": filename, "note": "entities require OPENAI_API_KEY"})

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize the document in 2-3 sentences and extract up to 8 key entities "
                        'as JSON: {"entities":[{"name":"...","type":"..."}]}'
                    ),
                },
                {"role": "user", "content": f"Filename: {filename}\n\n{excerpt}"},
            ],
            temperature=0.1,
        )
        content = (response.choices[0].message.content or "").strip()
        summary = content.split("{")[0].strip() if "{" in content else content
        entities_json = content[content.find("{") :] if "{" in content else json.dumps({"raw": content})
        return summary[:2000], entities_json[:4000]
    except Exception:  # noqa: BLE001
        return excerpt[:400], None
