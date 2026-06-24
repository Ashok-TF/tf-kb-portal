from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    *,
    user_email: str,
    action: str,
    kb_id: str | None = None,
    document_id: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_email=user_email,
            action=action,
            kb_id=kb_id,
            document_id=document_id,
            detail=detail,
        )
    )
    db.commit()
