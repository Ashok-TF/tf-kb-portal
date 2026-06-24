from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import Document, KnowledgeBase, WikiArticle
from app.schemas import CrawlRequest, CrawlResponse, WikiArticleOut
from app.services.access import ensure_kb_access
from app.services.audit import log_audit
from app.services.crawler import crawl_site
from app.services.pipeline import process_document
from app.services.wiki import refresh_wiki_for_kb

router = APIRouter(prefix="/api", tags=["crawl", "wiki"])


def _ingest_crawled_page(db: Session, kb_id: str, url: str, text: str, settings: Settings) -> str:
    slug = url.replace("https://", "").replace("http://", "")[:80].replace("/", "_")
    filename = f"crawl_{slug}.txt"
    doc = Document(
        kb_id=kb_id,
        filename=filename,
        content_type="text/plain",
        file_extension="txt",
        status="pending",
        source_url=url,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    dest = settings.upload_path / f"{doc.id}.txt"
    dest.write_text(text, encoding="utf-8")
    doc.storage_path = str(dest)
    doc.size_bytes = len(text.encode("utf-8"))
    db.commit()
    return doc.id


def _run_crawl(kb_id: str, url: str, max_depth: int) -> None:
    settings = get_settings()
    pages = crawl_site(url, max_depth)
    db = SessionLocal()
    try:
        for page_url, text in pages:
            doc_id = _ingest_crawled_page(db, kb_id, page_url, text, settings)
            process_document(doc_id)
    finally:
        db.close()


@router.post("/knowledge-bases/{kb_id}/crawl", response_model=CrawlResponse, status_code=202)
def crawl_kb_site(
    kb_id: str,
    payload: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email: str = Depends(current_user),
) -> CrawlResponse:
    ensure_kb_access(db, email, kb_id)
    background_tasks.add_task(_run_crawl, kb_id, payload.url, payload.max_depth)
    log_audit(
        db,
        user_email=email,
        action="crawl_start",
        kb_id=kb_id,
        detail=f"{payload.url} depth={payload.max_depth}",
    )
    return CrawlResponse(
        status="accepted",
        message="Crawl started. Pages will appear as documents when processing completes.",
        pages_crawled=0,
    )


@router.get("/knowledge-bases/{kb_id}/wiki", response_model=list[WikiArticleOut])
def list_wiki_articles(
    kb_id: str,
    db: Session = Depends(get_db),
    email: str = Depends(current_user),
) -> list[WikiArticle]:
    ensure_kb_access(db, email, kb_id)
    return list(db.scalars(select(WikiArticle).where(WikiArticle.kb_id == kb_id)).all())


@router.post("/knowledge-bases/{kb_id}/wiki/refresh", response_model=WikiArticleOut)
def refresh_wiki(
    kb_id: str,
    db: Session = Depends(get_db),
    email: str = Depends(current_user),
) -> WikiArticle:
    ensure_kb_access(db, email, kb_id)
    article = refresh_wiki_for_kb(db, kb_id)
    if article is None:
        raise HTTPException(status_code=404, detail="No ready documents to build wiki from")
    return article
