"""Simple, dependency-free text chunker.

Splits on character length with overlap, preferring to break on paragraph or
sentence boundaries so chunks stay readable.
"""

from __future__ import annotations

import re

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    if overlap >= chunk_size:
        overlap = chunk_size // 4

    # First collapse into paragraphs, then pack paragraphs into chunks.
    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            # Flush current buffer, then hard-split the long paragraph.
            if buffer:
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_hard_split(para, chunk_size, overlap))
            continue

        if not buffer:
            buffer = para
        elif len(buffer) + 2 + len(para) <= chunk_size:
            buffer = f"{buffer}\n\n{para}"
        else:
            chunks.append(buffer)
            buffer = para

    if buffer:
        chunks.append(buffer)

    return [c.strip() for c in chunks if c.strip()]


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap
    return chunks
