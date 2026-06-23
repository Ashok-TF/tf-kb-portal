"""End-to-end ingestion pipeline.

extract text -> chunk -> embed -> upsert to vector store.

Runs in a FastAPI BackgroundTask so uploads return immediately (HTTP 202) and
the document status transitions pending -> processing -> ready/failed.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import get_settings
from app.database import SessionLocal
from app.models import Document
from app.services.chunk import chunk_text
from app.services.embeddings import get_embedder
from app.services.extract import ExtractionError, extract_text
from app.services.vectorstore import VectorRecord, get_vector_store

logger = logging.getLogger("kb.pipeline")


def namespace_for_kb(kb_id: str) -> str:
    return f"kb-{kb_id}"


def process_document(document_id: str) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("Document %s not found; skipping", document_id)
            return

        doc.status = "processing"
        doc.error = None
        db.commit()

        try:
            text = extract_text(Path(doc.storage_path), doc.content_type)
        except ExtractionError as exc:
            _fail(db, doc, str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            _fail(db, doc, f"Extraction failed: {exc}")
            return

        char_count = len(text)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            _fail(db, doc, "No extractable text content found in the file.")
            return

        try:
            embedder = get_embedder(settings)
            vectors = embedder.embed(chunks)
            store = get_vector_store(settings, embedder.dim)
        except Exception as exc:  # noqa: BLE001
            _fail(db, doc, f"Embedding/vector-store init failed: {exc}")
            return

        records = [
            VectorRecord(
                id=f"{doc.id}::{i}",
                values=vec,
                metadata={
                    "document_id": doc.id,
                    "kb_id": doc.kb_id,
                    "filename": doc.filename,
                    "chunk_index": i,
                    "text": chunks[i][:2000],
                },
            )
            for i, vec in enumerate(vectors)
        ]

        try:
            store.upsert(records, namespace=namespace_for_kb(doc.kb_id))
        except Exception as exc:  # noqa: BLE001
            _fail(db, doc, f"Vector upsert failed: {exc}")
            return

        doc.status = "ready"
        doc.chunk_count = len(chunks)
        doc.char_count = char_count
        doc.error = None
        db.commit()
        logger.info("Processed document %s: %d chunks", doc.id, len(chunks))
    finally:
        db.close()


def _fail(db, doc: Document, message: str) -> None:
    logger.error("Document %s failed: %s", doc.id, message)
    doc.status = "failed"
    doc.error = message[:2000]
    db.commit()


def delete_document_vectors(kb_id: str, document_id: str) -> None:
    settings = get_settings()
    embedder = get_embedder(settings)
    store = get_vector_store(settings, embedder.dim)
    store.delete_by_document(document_id, namespace=namespace_for_kb(kb_id))


def delete_kb_vectors(kb_id: str) -> None:
    settings = get_settings()
    embedder = get_embedder(settings)
    store = get_vector_store(settings, embedder.dim)
    store.delete_namespace(namespace=namespace_for_kb(kb_id))
