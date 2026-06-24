from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KbManagerAssignment, KnowledgeBase, User


def ensure_kb_access(db: Session, email: str, kb_id: str) -> KnowledgeBase:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        # Legacy single-user mode: portal admin from env is treated as admin.
        return kb
    if user.role == "admin":
        return kb
    if user.role == "consumer":
        raise HTTPException(status_code=403, detail="Not authorized for this knowledge base")
    assigned = db.scalar(
        select(KbManagerAssignment).where(
            KbManagerAssignment.user_id == user.id,
            KbManagerAssignment.kb_id == kb_id,
        )
    )
    if assigned is None:
        raise HTTPException(status_code=403, detail="Not authorized for this knowledge base")
    return kb


def list_accessible_kb_ids(db: Session, email: str) -> list[str] | None:
    """Return None if user can access all KBs (admin / legacy)."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.role == "admin":
        return None
    if user.role == "consumer":
        return []
    rows = db.scalars(
        select(KbManagerAssignment.kb_id).where(KbManagerAssignment.user_id == user.id)
    ).all()
    return list(rows)
