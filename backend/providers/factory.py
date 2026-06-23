"""Provider factory — creates the configured LLM provider at startup."""
from __future__ import annotations

import logging

from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)


def get_provider() -> LLMProvider:
    """Instantiate and return the LLM provider specified by LLM_PROVIDER in config.

    Supported values:
        gemini  — Google Gemini via google-genai (API key or Vertex AI)
        openai  — OpenAI via openai SDK (requires OPENAI_API_KEY)
    """
    from backend.config import settings

    provider_name = settings.llm_provider.lower()

    if provider_name == "gemini":
        from google import genai
        from backend.providers.gemini_provider import GeminiProvider

        if settings.google_api_key and not settings.gemini_use_vertex:
            logger.info("LLM provider: Gemini (API-key mode, model=%s)", settings.gemini_model)
            client = genai.Client(api_key=settings.google_api_key)
        else:
            logger.info(
                "LLM provider: Gemini (Vertex AI mode, project=%s, model=%s)",
                settings.google_cloud_project,
                settings.gemini_model,
            )
            client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
        return GeminiProvider(client=client, model=settings.gemini_model)

    if provider_name == "openai":
        from backend.providers.openai_provider import OpenAIProvider

        if not settings.openai_api_key:
            raise ValueError(
                "LLM_PROVIDER=openai requires OPENAI_API_KEY to be set."
            )
        logger.info("LLM provider: OpenAI (model=%s)", settings.openai_model)
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider_name}'. Supported: 'gemini', 'openai'."
    )
