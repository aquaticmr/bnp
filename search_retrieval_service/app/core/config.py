import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class SearchServiceSettings(BaseSettings):
    APP_NAME: str = 'Reg IRIS Search & Retrieval Service'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = False
    API_PREFIX: str = '/api/v1'
    HOST: str = '0.0.0.0'
    PORT: int = 8001
    CORS_ORIGINS: List[str] = ['*']
    REQUIRE_AUTH: bool = False
    API_BEARER_TOKEN: str = 'reg-iris-demo-token-2026'
    ELASTICSEARCH_URL: str = 'http://localhost:9200'
    ELASTICSEARCH_INDEX: str = 'regulatory_clauses'
    ELASTICSEARCH_TIMEOUT_SECONDS: int = 5
    CHROMADB_HOST: str = 'localhost'
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = 'reg-iris-collection'
    CHROMADB_PERSIST_DIR: str = str(BASE_DIR / 'chroma_storage')
    EMBEDDING_MODEL_NAME: str = 'all-MiniLM-L6-v2'
    EMBEDDING_BATCH_SIZE: int = 64
    VECTOR_DIMENSION: int = 384
    OLLAMA_BASE_URL: str = 'http://localhost:11434'
    OLLAMA_MODEL: str = 'mistral:instruct'
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='ignore')
settings = SearchServiceSettings()