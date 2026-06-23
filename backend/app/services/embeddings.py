"""Embedding providers.

Two implementations:

* FakeEmbedder  - an offline "feature hashing" lexical embedder. No API keys,
  no heavy ML dependencies. It maps shared vocabulary to similar vectors, so
  cosine search returns keyword-relevant results. Great for local dev/demo.
* OpenAIEmbedder - real semantic embeddings via the OpenAI API.

Pick the provider with EMBEDDING_PROVIDER in your .env.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from app.config import Settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Embedder(ABC):
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class FakeEmbedder(Embedder):
    """Deterministic lexical embedder using the hashing trick."""

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = _TOKEN_RE.findall(text.lower())
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        # L2 normalize so dot product == cosine similarity.
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Install the 'openai' package to use the OpenAI embedder") from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model
        # Known dimensions for common models; default to 1536.
        self.dim = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}.get(model, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "openai":
        return OpenAIEmbedder(settings.openai_api_key, settings.openai_embedding_model)
    return FakeEmbedder(dim=settings.embedding_dim)
