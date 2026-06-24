from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import KnowledgeBase
from app.schemas import ChatRequest, ChatResponse
from app.services.access import list_accessible_kb_ids
from app.services.audit import log_audit
from app.services.rag import global_chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def global_agent_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    email: str = Depends(current_user),
) -> ChatResponse:
    allowed = list_accessible_kb_ids(db, email)
    q = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
    kbs = list(db.scalars(q).all())
    if allowed is not None:
        kbs = [kb for kb in kbs if kb.id in allowed]
    if not kbs:
        raise HTTPException(status_code=404, detail="No accessible knowledge bases")

    response = global_chat(db, settings, kbs, payload.query, payload.top_k)
    log_audit(db, user_email=email, action="global_chat", detail=payload.query[:500])
    return response
