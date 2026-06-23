import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Document, KnowledgeBase
from app.schemas import DocumentOut
from app.services.pipeline import delete_document_vectors, process_document

router = APIRouter(prefix="/api", tags=["documents"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    "pdf", "txt", "md", "markdown", "csv", "json", "log",
    "docx", "pptx", "xlsx", "xlsm",
    "png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp",
}


@router.get("/knowledge-bases/{kb_id}/documents", response_model=list[DocumentOut])
def list_documents(
    kb_id: str, db: Session = Depends(get_db), _: str = Depends(current_user)
) -> list[Document]:
    if db.get(KnowledgeBase, kb_id) is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return list(
        db.scalars(
            select(Document)
            .where(Document.kb_id == kb_id)
            .order_by(Document.created_at.desc())
        ).all()
    )


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(current_user),
) -> Document:
    if db.get(KnowledgeBase, kb_id) is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Create the row first so we have an id for the storage filename.
    doc = Document(
        kb_id=kb_id,
        filename=filename,
        content_type=file.content_type,
        file_extension=ext,
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    dest: Path = settings.upload_path / f"{doc.id}.{ext}" if ext else settings.upload_path / doc.id
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    out.close()
                    dest.unlink(missing_ok=True)
                    db.delete(doc)
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds the 50 MB limit",
                    )
                out.write(chunk)
    finally:
        file.file.close()

    doc.storage_path = str(dest)
    doc.size_bytes = size
    db.commit()
    db.refresh(doc)

    # Kick off async processing.
    background_tasks.add_task(process_document, doc.id)
    return doc


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str, db: Session = Depends(get_db), _: str = Depends(current_user)
) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    download: bool = Query(False, description="Force download instead of inline preview"),
    db: Session = Depends(get_db),
    _: str = Depends(current_user),
) -> FileResponse:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_path:
        raise HTTPException(status_code=404, detail="File not available")
    path = Path(doc.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found on disk")

    disposition = "attachment" if download else "inline"
    media_type = doc.content_type or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        filename=doc.filename,
        content_disposition_type=disposition,
    )


@router.post("/documents/{document_id}/reindex", response_model=DocumentOut, status_code=202)
def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(current_user),
) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = "pending"
    db.commit()
    db.refresh(doc)
    background_tasks.add_task(process_document, doc.id)
    return doc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str, db: Session = Depends(get_db), _: str = Depends(current_user)
) -> None:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    kb_id = doc.kb_id
    if doc.storage_path:
        Path(doc.storage_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    try:
        delete_document_vectors(kb_id, document_id)
    except Exception:
        pass
