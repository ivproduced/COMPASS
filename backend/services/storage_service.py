"""
Cloud Storage Service
Handles OSCAL output storage, diagram storage, and signed URL generation.
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta

from google.cloud import storage
from google.cloud.storage import Blob

from backend.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self._client: storage.Client | None = None

    def _get_client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client(project=settings.google_cloud_project)
        return self._client

    def _bucket(self) -> storage.Bucket:
        return self._get_client().bucket(settings.gcs_bucket_oscal)

    # ------------------------------------------------------------------
    # OSCAL Documents
    # ------------------------------------------------------------------

    def upload_oscal(
        self,
        session_id: str,
        doc_type: str,
        content: dict,
        timestamp: str,
    ) -> str:
        """
        Upload an OSCAL JSON document to GCS.
        Returns the GCS object path (gs://bucket/path).
        """
        blob_name = f"sessions/{session_id}/oscal/{doc_type}_{timestamp}.json"
        blob: Blob = self._bucket().blob(blob_name)
        blob.upload_from_string(
            data=json.dumps(content, indent=2),
            content_type="application/json",
        )
        gcs_path = f"gs://{settings.gcs_bucket_oscal}/{blob_name}"
        logger.info("Uploaded OSCAL %s to %s", doc_type, gcs_path)
        return gcs_path

    def download_oscal_bytes(self, gcs_path: str) -> bytes:
        """Download an OSCAL document from GCS and return raw bytes."""
        prefix = f"gs://{settings.gcs_bucket_oscal}/"
        blob_name = gcs_path[len(prefix):] if gcs_path.startswith(prefix) else gcs_path
        blob: Blob = self._bucket().blob(blob_name)
        return blob.download_as_bytes()

    def generate_signed_url(self, gcs_path: str, expiry_minutes: int = 60) -> str:
        """Generate a signed download URL for a GCS object."""
        # Strip gs://bucket/ prefix to get blob name
        prefix = f"gs://{settings.gcs_bucket_oscal}/"
        if gcs_path.startswith(prefix):
            blob_name = gcs_path[len(prefix):]
        else:
            blob_name = gcs_path

        blob: Blob = self._bucket().blob(blob_name)
        url = blob.generate_signed_url(
            expiration=timedelta(minutes=expiry_minutes),
            method="GET",
            version="v4",
        )
        return url

    # ------------------------------------------------------------------
    # Architecture Diagrams
    # ------------------------------------------------------------------

    def upload_diagram(
        self,
        session_id: str,
        filename: str,
        data: bytes,
        content_type: str = "image/png",
    ) -> str:
        """Upload an architecture diagram; return GCS path."""
        blob_name = f"sessions/{session_id}/diagrams/{filename}"
        blob: Blob = self._bucket().blob(blob_name)
        blob.upload_from_string(data=data, content_type=content_type)
        gcs_path = f"gs://{settings.gcs_bucket_oscal}/{blob_name}"
        logger.info("Uploaded diagram %s to %s", filename, gcs_path)
        return gcs_path

    def get_diagram_bytes(self, gcs_path: str) -> bytes:
        """Download a diagram for forwarding to Gemini Vision."""
        prefix = f"gs://{settings.gcs_bucket_oscal}/"
        blob_name = gcs_path[len(prefix):] if gcs_path.startswith(prefix) else gcs_path
        blob: Blob = self._bucket().blob(blob_name)
        return blob.download_as_bytes()

    # ------------------------------------------------------------------
    # Session Export
    # ------------------------------------------------------------------

    def export_session_json(self, session_id: str, session_data: dict, timestamp: str) -> str:
        """Export a complete session snapshot to GCS; return GCS path."""
        blob_name = f"sessions/{session_id}/exports/session_export_{timestamp}.json"
        blob: Blob = self._bucket().blob(blob_name)
        blob.upload_from_string(
            data=json.dumps(session_data, indent=2),
            content_type="application/json",
        )
        return f"gs://{settings.gcs_bucket_oscal}/{blob_name}"


storage_service = StorageService()
