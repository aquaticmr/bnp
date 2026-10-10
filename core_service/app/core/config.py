import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Reg IRIS Core Intelligence Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Authentication
    REQUIRE_AUTH: bool = False
    API_BEARER_TOKEN: str = "reg-iris-demo-token-2026"

    # Database (PostgreSQL with SQLite fallback)
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@localhost:5432/regiris"
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'regiris_local.db'}"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "regulatory_clauses"
    ELASTICSEARCH_TIMEOUT_SECONDS: int = 5

    # ChromaDB
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "reg-iris-collection"
    CHROMADB_PERSIST_DIR: str = str(BASE_DIR / "chroma_storage")

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 64
    VECTOR_DIMENSION: int = 384

    # LLM Settings (Local Ollama / OpenAI Compatible)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:instruct"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    # Storage & Data Paths
    DATA_DIR: Path = BASE_DIR / "data"
    RULES_PATH: Path = BASE_DIR / "data" / "rules" / "regulatory_rules.json"
    TRADES_PATH: Path = BASE_DIR / "data" / "trades" / "sample_trades.csv"
    SCHEMA_PATH: Path = BASE_DIR / "data" / "schema" / "reporting_schema.json"
    METADATA_PATH: Path = BASE_DIR / "data" / "metadata" / "doc_metadata.csv"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
