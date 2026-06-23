from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.database import get_db
from app.models import Document, KnowledgeBase
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseOut
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
    db: Session = Depends(get_db), _: str = Depends(current_user)
) -> list[KnowledgeBaseOut]:
    kbs = db.scalars(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())).all()
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
    return _to_out(db, kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
def get_knowledge_base(
    kb_id: str, db: Session = Depends(get_db), _: str = Depends(current_user)
) -> KnowledgeBaseOut:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return _to_out(db, kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: str, db: Session = Depends(get_db), _: str = Depends(current_user)
) -> None:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    db.delete(kb)
    db.commit()
    try:
        delete_kb_vectors(kb_id)
    except Exception:
        # Vector cleanup is best-effort; metadata is already gone.
        pass
