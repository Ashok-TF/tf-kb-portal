from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.database import get_db
from app.models import Document, KnowledgeBase
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate
from app.services.access import ensure_kb_access, list_accessible_kb_ids
from app.services.audit import log_audit
from app.services.pipeline import delete_kb_vectors

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


def _to_out(db: Session, kb: KnowledgeBase) -> KnowledgeBaseOut:
    total = db.scalar(select(func.count(Document.id)).where(Document.kb_id == kb.id)) or 0
    ready = (
        db.scalar(
            select(func.count(Document.id)).where(
                Document.kb_id == kb.id, Document.status == "ready"
            )
        )
        or 0
    )
    out = KnowledgeBaseOut.model_validate(kb)
    out.document_count = int(total)
    out.ready_count = int(ready)
    return out


@router.get("", response_model=list[KnowledgeBaseOut])
def list_knowledge_bases(
    db: Session = Depends(get_db), email: str = Depends(current_user)
) -> list[KnowledgeBaseOut]:
    allowed = list_accessible_kb_ids(db, email)
    q = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
    kbs = list(db.scalars(q).all())
    if allowed is not None:
        kbs = [kb for kb in kbs if kb.id in allowed]
    return [_to_out(db, kb) for kb in kbs]


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    email: str = Depends(current_user),
) -> KnowledgeBaseOut:
    kb = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        department=payload.department,
        created_by=email,
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    log_audit(db, user_email=email, action="kb_create", kb_id=kb.id, detail=kb.name)
    return _to_out(db, kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
def get_knowledge_base(
    kb_id: str, db: Session = Depends(get_db), email: str = Depends(current_user)
) -> KnowledgeBaseOut:
    kb = ensure_kb_access(db, email, kb_id)
    return _to_out(db, kb)


@router.patch("/{kb_id}", response_model=KnowledgeBaseOut)
def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    email: str = Depends(current_user),
) -> KnowledgeBaseOut:
    kb = ensure_kb_access(db, email, kb_id)
    if payload.name is not None:
        kb.name = payload.name
    if payload.description is not None:
        kb.description = payload.description
    if payload.department is not None:
        kb.department = payload.department
    db.commit()
    db.refresh(kb)
    log_audit(db, user_email=email, action="kb_update", kb_id=kb_id)
    return _to_out(db, kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: str, db: Session = Depends(get_db), email: str = Depends(current_user)
) -> None:
    kb = ensure_kb_access(db, email, kb_id)
    db.delete(kb)
    db.commit()
    log_audit(db, user_email=email, action="kb_delete", kb_id=kb_id)
    try:
        delete_kb_vectors(kb_id)
    except Exception:
        pass
