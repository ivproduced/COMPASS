"""
Semantic Control Search via Vertex AI Vector Search.
Falls back to keyword search in the local catalog when Vector Search is
unavailable (e.g. during local development).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


def _get_vector_service():
    """Lazy import to avoid circular deps and allow graceful fallback."""
    try:
        from backend.services.vector_service import vector_service  # type: ignore
        return vector_service
    except Exception:
        return None


def search_controls_impl(
    query: str,
    family_filter: str | None = None,
    top_k: int = 10,
) -> dict:
    """
    Semantic search over the NIST 800-53 control corpus using Vertex AI Vector Search.
    Falls back to keyword search when Vector Search is unavailable.

    Args:
        query:         Natural language query (e.g. "web application firewall boundary protection").
        family_filter: Optional family code to restrict results (e.g. "SC").
        top_k:         Number of results to return (default 10).

    Returns:
        Dict with controls list, scores, and search method used.
    """
    svc = _get_vector_service()

    if svc is not None:
        try:
            # Run async method in sync context (agents call tools synchronously)
            loop = asyncio.new_event_loop()
            results: list[dict[str, Any]] = loop.run_until_complete(
                svc.query(query=query, top_k=top_k, family_filter=family_filter)
            )
            loop.close()
            return {
                "controls": results,
                "count": len(results),
                "search_method": "vector_search",
            }
        except Exception as exc:
            logger.warning("Vector Search failed, falling back to keyword: %s", exc)

    # Keyword fallback
    from .control_lookup import control_lookup_impl

    result = control_lookup_impl(keyword=query, family=family_filter, limit=top_k)
    result["search_method"] = "keyword_fallback"
    return result


search_controls_tool = FunctionTool(func=search_controls_impl)
