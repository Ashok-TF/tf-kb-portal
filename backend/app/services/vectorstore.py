"""Vector store providers.

* LocalVectorStore - persists vectors + metadata to a JSON file on disk and
  does brute-force cosine search with numpy. Zero external dependencies.
* PineconeVectorStore - upserts/queries a Pinecone managed index.

Pick the provider with VECTOR_STORE in your .env.
"""

from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.config import Settings


@dataclass
class VectorRecord:
    id: str
    values: list[float]
    metadata: dict[str, Any]


@dataclass
class QueryMatch:
    id: str
    score: float
    metadata: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, records: list[VectorRecord], namespace: str) -> None:
        ...

    @abstractmethod
    def query(self, vector: list[float], top_k: int, namespace: str) -> list[QueryMatch]:
        ...

    @abstractmethod
    def delete_by_document(self, document_id: str, namespace: str) -> None:
        ...

    @abstractmethod
    def delete_namespace(self, namespace: str) -> None:
        ...


class LocalVectorStore(VectorStore):
    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "vector_index.json"
        self._lock = threading.Lock()
        self._data: dict[str, list[dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data), encoding="utf-8")

    def upsert(self, records: list[VectorRecord], namespace: str) -> None:
        with self._lock:
            bucket = self._data.setdefault(namespace, [])
            existing = {r.id for r in records}
            bucket = [r for r in bucket if r["id"] not in existing]
            for rec in records:
                bucket.append({"id": rec.id, "values": rec.values, "metadata": rec.metadata})
            self._data[namespace] = bucket
            self._save()

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[QueryMatch]:
        with self._lock:
            bucket = list(self._data.get(namespace, []))
        if not bucket:
            return []

        matrix = np.array([r["values"] for r in bucket], dtype=np.float32)
        q = np.array(vector, dtype=np.float32)

        # Cosine similarity (vectors may not be normalized for OpenAI).
        denom = (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)) + 1e-10
        scores = (matrix @ q) / denom

        top_idx = np.argsort(-scores)[:top_k]
        return [
            QueryMatch(id=bucket[i]["id"], score=float(scores[i]), metadata=bucket[i]["metadata"])
            for i in top_idx
        ]

    def delete_by_document(self, document_id: str, namespace: str) -> None:
        with self._lock:
            bucket = self._data.get(namespace, [])
            self._data[namespace] = [
                r for r in bucket if r["metadata"].get("document_id") != document_id
            ]
            self._save()

    def delete_namespace(self, namespace: str) -> None:
        with self._lock:
            self._data.pop(namespace, None)
            self._save()


class PineconeVectorStore(VectorStore):
    def __init__(self, settings: Settings, dim: int) -> None:
        try:
            from pinecone import Pinecone, ServerlessSpec
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Install the 'pinecone' package to use VECTOR_STORE=pinecone") from exc

        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required when VECTOR_STORE=pinecone")

        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index_name = settings.pinecone_index

        existing = {i["name"] for i in self._pc.list_indexes()}
        if self._index_name not in existing:
            self._pc.create_index(
                name=self._index_name,
                dimension=dim,
                metric="cosine",
                spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
            )
        self._index = self._pc.Index(self._index_name)

    def upsert(self, records: list[VectorRecord], namespace: str) -> None:
        if not records:
            return
        vectors = [{"id": r.id, "values": r.values, "metadata": r.metadata} for r in records]
        # Pinecone recommends batches of <= 100.
        for i in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[i : i + 100], namespace=namespace)

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[QueryMatch]:
        res = self._index.query(
            vector=vector, top_k=top_k, namespace=namespace, include_metadata=True
        )
        return [
            QueryMatch(id=m["id"], score=float(m["score"]), metadata=dict(m.get("metadata") or {}))
            for m in res.get("matches", [])
        ]

    def delete_by_document(self, document_id: str, namespace: str) -> None:
        try:
            self._index.delete(filter={"document_id": document_id}, namespace=namespace)
        except Exception:
            # Metadata filtering on delete isn't available on all Pinecone tiers.
            pass

    def delete_namespace(self, namespace: str) -> None:
        try:
            self._index.delete(delete_all=True, namespace=namespace)
        except Exception:
            pass


_store_singleton: VectorStore | None = None


def get_vector_store(settings: Settings, dim: int) -> VectorStore:
    global _store_singleton
    if _store_singleton is not None:
        return _store_singleton

    if settings.vector_store == "pinecone":
        _store_singleton = PineconeVectorStore(settings, dim)
    else:
        _store_singleton = LocalVectorStore(settings.data_path)
    return _store_singleton
