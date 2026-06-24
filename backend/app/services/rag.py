from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import KnowledgeBase
from app.schemas import ChatResponse, Citation, SelectedKb
from app.services.embeddings import get_embedder
from app.services.llm import generate_answer
from app.services.pipeline import namespace_for_kb
from app.services.vectorstore import get_vector_store


def _retrieve_for_kb(
    settings: Settings, kb: KnowledgeBase, query: str, top_k: int
) -> list[Citation]:
    embedder = get_embedder(settings)
    store = get_vector_store(settings, embedder.dim)
    query_vec = embedder.embed_one(query)
    matches = store.query(query_vec, top_k=top_k, namespace=namespace_for_kb(kb.id))

    citations: list[Citation] = []
    for m in matches:
        citations.append(
            Citation(
                document_id=str(m.metadata.get("document_id", "")),
                filename=str(m.metadata.get("filename", "")),
                kb_id=kb.id,
                kb_name=kb.name,
                chunk_index=int(m.metadata.get("chunk_index", 0)),
                score=round(m.score, 4),
                excerpt=str(m.metadata.get("text", ""))[:500],
            )
        )
    return citations


def chat_for_kb(db: Session, settings: Settings, kb: KnowledgeBase, query: str, top_k: int = 5) -> ChatResponse:
    citations = _retrieve_for_kb(settings, kb, query, top_k)
    answer = generate_answer(settings, query, [c.excerpt for c in citations if c.excerpt])
    return ChatResponse(
        answer=answer,
        citations=citations,
        selected_kbs=[SelectedKb(id=kb.id, name=kb.name, score=1.0)],
    )


def score_kb(kb: KnowledgeBase, query: str) -> float:
    q = query.lower()
    score = 0.0
    for field in (kb.name, kb.description or "", kb.department or ""):
        fl = field.lower()
        if not fl:
            continue
        if q in fl or fl in q:
            score += 2.0
        for word in q.split():
            if len(word) > 3 and word in fl:
                score += 0.5
    return score


def global_chat(
    db: Session, settings: Settings, kbs: list[KnowledgeBase], query: str, top_k: int = 5, max_kbs: int = 3
) -> ChatResponse:
    ranked = sorted(((score_kb(kb, query), kb) for kb in kbs), key=lambda x: x[0], reverse=True)
    selected = [kb for s, kb in ranked if s > 0][:max_kbs] or ([ranked[0][1]] if ranked else [])

    all_citations: list[Citation] = []
    seen: set[str] = set()
    for kb in selected:
        for c in _retrieve_for_kb(settings, kb, query, top_k):
            key = f"{c.document_id}:{c.chunk_index}"
            if key in seen:
                continue
            seen.add(key)
            all_citations.append(c)

    all_citations.sort(key=lambda c: c.score, reverse=True)
    all_citations = all_citations[: top_k * 2]

    answer = generate_answer(settings, query, [c.excerpt for c in all_citations if c.excerpt])
    selected_kbs = [
        SelectedKb(id=kb.id, name=kb.name, score=round(score_kb(kb, query), 2)) for kb in selected
    ]
    return ChatResponse(answer=answer, citations=all_citations, selected_kbs=selected_kbs)
