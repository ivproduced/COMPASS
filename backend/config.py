"""
COMPASS Configuration
Loads all environment variables and provides typed config constants.
"""
from __future__ import annotations

import os
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
    google_cloud_project: str = "compass-fedramp"
    google_cloud_location: str = "us-central1"

    # -------------------------------------------------------------------
    # Gemini
    # -------------------------------------------------------------------
    gemini_model: str = "gemini-2.5-pro"
    gemini_voice: str = "Kore"

    # -------------------------------------------------------------------
    # Firestore
    # -------------------------------------------------------------------
    firestore_database: str = "compass"

    # -------------------------------------------------------------------
    # Cloud Storage
    # -------------------------------------------------------------------
    gcs_bucket_oscal: str = "compass-fedramp-oscal"

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
    cors_origins: list[str] = ["http://localhost:3000", "https://compass-fedramp.web.app"]

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
