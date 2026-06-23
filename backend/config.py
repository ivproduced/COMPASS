"""
COMPASS Configuration
Loads all environment variables and provides typed config constants.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------
    # Google Cloud
    # -------------------------------------------------------------------
    google_cloud_project: str = "gen-lang-client-0235375201"
    google_cloud_location: str = "us-central1"

    # -------------------------------------------------------------------
    # LLM Provider selection
    # -------------------------------------------------------------------
    llm_provider: str = "gemini"          # "gemini" | "openai"

    # -------------------------------------------------------------------
    # Gemini (used when llm_provider = "gemini")
    # -------------------------------------------------------------------
    gemini_model: str = "gemini-2.5-pro"
    gemini_live_model: str = "gemini-2.5-flash-native-audio-latest"  # Live API model available for this API key
    gemini_voice: str = "Kore"
    google_api_key: str = ""              # Set for API-key mode (Developer API key)
    gemini_use_vertex: bool = False       # False → use Developer API key (Vertex Live API not yet GA)

    # -------------------------------------------------------------------
    # OpenAI (used when llm_provider = "openai")
    # -------------------------------------------------------------------
    openai_api_key: str = ""              # Required when llm_provider = "openai"
    openai_model: str = "gpt-4o"         # Text/reasoning model for sidecar + chat

    # -------------------------------------------------------------------
    # Firestore
    # -------------------------------------------------------------------
    firestore_database: str = "compass"

    # -------------------------------------------------------------------
    # Cloud Storage
    # -------------------------------------------------------------------
    gcs_bucket_oscal: str = "compass-hackathon-oscal"

    # -------------------------------------------------------------------
    # Vertex AI Vector Search
    # -------------------------------------------------------------------
    vector_search_index_endpoint: str = ""
    vector_search_index_id: str = ""
    vector_search_deployed_index_id: str = "compass_controls_deployed"
    embedding_model: str = "text-embedding-005"
    embedding_dimensions: int = 768
    vector_search_top_k: int = 10

    # -------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "https://compass-fedramp.web.app",
        "https://compass-backend-278165225404.us-central1.run.app",
    ]

    # -------------------------------------------------------------------
    # Session
    # -------------------------------------------------------------------
    session_inactivity_timeout_seconds: int = 900  # 15 minutes
    max_transcript_entries_loaded: int = 50

    # -------------------------------------------------------------------
    # OSCAL
    # -------------------------------------------------------------------
    oscal_version: str = "1.1.2"
    oscal_min_coverage_for_ssp: float = 0.80  # 80 % controls mapped before SSP gen

    # -------------------------------------------------------------------
    # Security (OWASP LLM Top 10 / Agentic Top 10 hardening)
    # -------------------------------------------------------------------
    # LLM10 / Agentic resource-exhaustion guards
    max_diagram_size_mb: int = 10
    max_sessions_per_user: int = 20
    max_transcript_limit: int = 100

    # Rate limiting (requests per window per client IP)
    rate_limit_websocket: int = 10       # WS connections / 60 s
    rate_limit_chat: int = 30            # chat requests  / 60 s
    rate_limit_session_create: int = 5   # new sessions   / 60 s
    rate_limit_diagram_upload: int = 10  # uploads        / 60 s
    rate_limit_default: int = 60         # all other       / 60 s

    # LLM06 / Agentic excessive-agency guards
    require_session_ownership_check: bool = True
    tool_execution_timeout_seconds: int = 30


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
