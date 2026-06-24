from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.access import ensure_kb_access
from app.services.audit import log_audit
from app.services.rag import chat_for_kb

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/knowledge-bases/{kb_id}/chat", response_model=ChatResponse)
def kb_chat(
    kb_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    email: str = Depends(current_user),
) -> ChatResponse:
    kb = ensure_kb_access(db, email, kb_id)
    response = chat_for_kb(db, settings, kb, payload.query, payload.top_k)
    log_audit(db, user_email=email, action="kb_chat", kb_id=kb_id, detail=payload.query[:500])
    return response
