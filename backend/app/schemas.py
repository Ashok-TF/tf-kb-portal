from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Auth ---
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    email: str


class MeResponse(BaseModel):
    email: str


# --- Knowledge bases ---
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    department: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    department: str | None = None


class KnowledgeBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    department: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    ready_count: int = 0


# --- Documents ---
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kb_id: str
    filename: str
    content_type: str | None
    file_extension: str | None
    size_bytes: int
    status: str
    chunk_count: int
    char_count: int
    error: str | None
    summary: str | None = None
    entities_json: str | None = None
    created_at: datetime
    updated_at: datetime


# --- Search ---
class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchMatch(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    score: float
    text: str


class SearchResponse(BaseModel):
    query: str
    matches: list[SearchMatch]


# --- Chat ---
class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    document_id: str
    filename: str
    kb_id: str
    kb_name: str | None = None
    chunk_index: int
    score: float
    excerpt: str


class SelectedKb(BaseModel):
    id: str
    name: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    selected_kbs: list[SelectedKb] = []


# --- Crawl ---
class CrawlRequest(BaseModel):
    url: str = Field(min_length=1)
    max_depth: int = Field(default=1, ge=1, le=3)


class CrawlResponse(BaseModel):
    status: str
    message: str
    pages_crawled: int = 0


# --- Audit ---
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_email: str
    action: str
    kb_id: str | None
    document_id: str | None
    detail: str | None
    created_at: datetime


# --- Wiki ---
class WikiArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kb_id: str
    title: str
    summary: str
    source_documents: str | None
    created_at: datetime
    updated_at: datetime
