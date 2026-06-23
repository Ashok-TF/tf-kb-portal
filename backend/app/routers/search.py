from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import KnowledgeBase
from app.schemas import SearchMatch, SearchRequest, SearchResponse
from app.services.embeddings import get_embedder
from app.services.pipeline import namespace_for_kb
from app.services.vectorstore import get_vector_store

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/knowledge-bases/{kb_id}/search", response_model=SearchResponse)
def search(
    kb_id: str,
    payload: SearchRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(current_user),
) -> SearchResponse:
    if db.get(KnowledgeBase, kb_id) is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    embedder = get_embedder(settings)
    store = get_vector_store(settings, embedder.dim)

    query_vec = embedder.embed_one(payload.query)
    matches = store.query(query_vec, top_k=payload.top_k, namespace=namespace_for_kb(kb_id))

    results = [
        SearchMatch(
            document_id=str(m.metadata.get("document_id", "")),
            filename=str(m.metadata.get("filename", "")),
            chunk_index=int(m.metadata.get("chunk_index", 0)),
            score=round(m.score, 4),
            text=str(m.metadata.get("text", "")),
        )
        for m in matches
    ]
    return SearchResponse(query=payload.query, matches=results)
