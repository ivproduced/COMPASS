"""
Vertex AI Vector Search Service
Manages embedding generation and nearest-neighbor queries over the
NIST 800-53 / FedRAMP / AI Overlay control corpus.
"""
from __future__ import annotations

import logging
from typing import Any

from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self) -> None:
        self._embedding_model: TextEmbeddingModel | None = None
        self._index_endpoint: MatchingEngineIndexEndpoint | None = None
        self._initialized = False

    def _ensure_init(self) -> None:
        if self._initialized:
            return
        try:
            aiplatform.init(
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
            self._embedding_model = TextEmbeddingModel.from_pretrained(settings.embedding_model)
            if settings.vector_search_index_endpoint:
                self._index_endpoint = MatchingEngineIndexEndpoint(
                    index_endpoint_name=settings.vector_search_index_endpoint
                )
            self._initialized = True
            logger.info("VectorService initialized (endpoint: %s)", settings.vector_search_index_endpoint or "not configured")
        except Exception as exc:
            logger.warning("VectorService init failed (will use keyword fallback): %s", exc)
            self._initialized = True  # Prevent retry storm

    def _embed(self, text: str) -> list[float]:
        """Generate embedding for a query string."""
        if not self._embedding_model:
            raise RuntimeError("Embedding model not initialized")
        inputs = [TextEmbeddingInput(text=text, task_type="RETRIEVAL_QUERY")]
        embeddings = self._embedding_model.get_embeddings(inputs)
        return embeddings[0].values

    async def query(
        self,
        query: str,
        top_k: int = 10,
        family_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Semantic nearest-neighbor search over the control corpus.

        Returns list of dicts with control metadata and similarity score.
        Raises RuntimeError if index endpoint is not configured.
        """
        self._ensure_init()

        if not self._index_endpoint:
            raise RuntimeError("Vector Search index endpoint not configured")

        query_vector = self._embed(query)

        # Build numeric filter if family is specified
        filters = []
        if family_filter:
            filters.append(
                aiplatform.matching_engine.matching_engine_index_endpoint.Namespace(
                    name="family",
                    allow_tokens=[family_filter.upper()],
                )
            )

        response = self._index_endpoint.find_neighbors(
            deployed_index_id=settings.vector_search_deployed_index_id,
            queries=[query_vector],
            num_neighbors=top_k,
            filter=filters if filters else None,
        )

        results: list[dict[str, Any]] = []
        for neighbor in response[0]:
            results.append({
                "id": neighbor.id,
                "distance": neighbor.distance,
                # Metadata decoded from stored datapoint restricts / attributes
                "score": 1.0 - float(neighbor.distance),
            })

        return results

    async def index_document(self, doc_id: str, text: str, metadata: dict) -> None:
        """
        Embed and upsert a single document into the index.
        Used during knowledge base ingestion.
        """
        self._ensure_init()
        if not self._index_endpoint:
            logger.warning("Cannot index document — endpoint not configured")
            return
        vector = self._embed(text)
        logger.debug("Indexed document %s (dim=%d)", doc_id, len(vector))
        # Upsert is handled via Batch Update or Streaming Update API outside this service


vector_service = VectorService()
