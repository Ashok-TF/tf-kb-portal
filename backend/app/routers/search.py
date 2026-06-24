from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas import SearchMatch, SearchRequest, SearchResponse
from app.services.access import ensure_kb_access
from app.services.audit import log_audit
from app.services.embeddings import get_embedder
from app.services.pipeline import namespace_for_kb
from app.services.vectorstore import get_vector_store

router = APIRouter(prefix="/api", tags=["search"])


def _hybrid_boost(query: str, text: str, vector_score: float) -> float:
    """Lightweight hybrid: boost vector score when query terms appear in text."""
    boost = 0.0
    q_lower = query.lower()
    t_lower = text.lower()
    for word in q_lower.split():
        if len(word) > 2 and word in t_lower:
            boost += 0.05
    return round(min(vector_score + boost, 1.0), 4)


@router.post("/knowledge-bases/{kb_id}/search", response_model=SearchResponse)
def search(
    kb_id: str,
    payload: SearchRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    email: str = Depends(current_user),
) -> SearchResponse:
    ensure_kb_access(db, email, kb_id)

    embedder = get_embedder(settings)
    store = get_vector_store(settings, embedder.dim)

    query_vec = embedder.embed_one(payload.query)
    matches = store.query(query_vec, top_k=payload.top_k, namespace=namespace_for_kb(kb_id))

    results = [
        SearchMatch(
            document_id=str(m.metadata.get("document_id", "")),
            filename=str(m.metadata.get("filename", "")),
            chunk_index=int(m.metadata.get("chunk_index", 0)),
            score=_hybrid_boost(payload.query, str(m.metadata.get("text", "")), m.score),
            text=str(m.metadata.get("text", "")),
        )
        for m in matches
    ]
    results.sort(key=lambda r: r.score, reverse=True)
    log_audit(db, user_email=email, action="search", kb_id=kb_id, detail=payload.query[:500])
    return SearchResponse(query=payload.query, matches=results)
