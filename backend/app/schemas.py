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
