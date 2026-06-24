from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, KnowledgeBase, WikiArticle


def refresh_wiki_for_kb(db: Session, kb_id: str) -> WikiArticle | None:
    docs = db.scalars(
        select(Document).where(Document.kb_id == kb_id, Document.status == "ready")
    ).all()
    if not docs:
        return None

    summaries = [d.summary for d in docs if d.summary]
    sources = ", ".join(d.filename for d in docs[:10])
    summary_text = (
        " ".join(summaries[:5])
        if summaries
        else f"Knowledge base contains {len(docs)} processed document(s)."
    )

    kb = db.get(KnowledgeBase, kb_id)
    kb_name = kb.name if kb else "Knowledge Base"

    existing = db.scalar(select(WikiArticle).where(WikiArticle.kb_id == kb_id))
    if existing:
        existing.title = f"Wiki — {kb_name}"
        existing.summary = summary_text[:4000]
        existing.source_documents = sources
        db.commit()
        db.refresh(existing)
        return existing

    article = WikiArticle(
        kb_id=kb_id,
        title=f"Wiki — {kb_name}",
        summary=summary_text[:4000],
        source_documents=sources,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article
