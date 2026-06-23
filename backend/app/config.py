from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "tfGPT KB Portal"
    cors_origins: str = "http://localhost:3001,http://localhost:3000"

    # Auth
    kb_portal_user: str = "admin@thoughtfocus.com"
    kb_portal_password: str = "tfKB@123"
    secret_key: str = "change-me-in-production-please"

    # Database / storage
    database_url: str = "sqlite:///./data/kb_portal.db"
    data_dir: str = "./data"

    # Embeddings
    embedding_provider: str = "fake"  # fake | openai
    embedding_dim: int = 512
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Vector store
    vector_store: str = "local"  # local | pinecone
    pinecone_api_key: str = ""
    pinecone_index: str = "tfgpt-kb"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Chunking
    chunk_size: int = 900
    chunk_overlap: int = 150

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def upload_path(self) -> Path:
        p = self.data_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
