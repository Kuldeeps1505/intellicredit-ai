from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    sync_database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "intellicredit-docs"
    minio_secure: bool = False

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # LLM — Ollama (local) primary, Gemini fallback
    anthropic_api_key: str = ""   # unused, kept for compat
    gemini_api_key: str = ""
    ollama_model: str = "mistral"
    ollama_base_url: str = "http://localhost:11434"

    # Sandbox.co.in
    sandbox_api_key: str = ""
    sandbox_secret_key: str = ""
    sandbox_base_url: str = "https://api.sandbox.co.in"

    # Account Aggregator (India Stack)
    aa_provider: str = "mock"          # "setu" | "sahamati" | "mock"
    setu_client_id: str = ""
    setu_client_secret: str = ""
    sahamati_token: str = ""
    fiu_id: str = "IntelliCredit-FIU-UAT"
    aa_id: str = "ONEMONEY-AA"

    # Tavily
    tavily_api_key: str = ""

    # eCourts
    ecourts_api_key: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "change_me"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()