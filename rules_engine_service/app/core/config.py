import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class RulesServiceSettings(BaseSettings):
    APP_NAME: str = 'Reg IRIS Rules Engine & Impact Scanner Service'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = False
    API_PREFIX: str = '/api/v1'
    HOST: str = '0.0.0.0'
    PORT: int = 8002
    CORS_ORIGINS: List[str] = ['*']
    REQUIRE_AUTH: bool = False
    API_BEARER_TOKEN: str = 'reg-iris-demo-token-2026'
    DATABASE_URL: str = 'postgresql://postgres:postgrespassword@localhost:5432/regiris'
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'regiris_rules_local.db'}"
    DATA_DIR: Path = BASE_DIR / 'data'
    RULES_PATH: Path = BASE_DIR / 'data' / 'rules' / 'regulatory_rules.json'
    TRADES_PATH: Path = BASE_DIR / 'data' / 'trades' / 'sample_trades.csv'
    SCHEMA_PATH: Path = BASE_DIR / 'data' / 'schema' / 'reporting_schema.json'
    METADATA_PATH: Path = BASE_DIR / 'data' / 'metadata' / 'doc_metadata.csv'
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='ignore')
settings = RulesServiceSettings()