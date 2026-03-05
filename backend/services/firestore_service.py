"""
Firestore Service
Handles all session and assessment state persistence.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient

from backend.config import settings

logger = logging.getLogger(__name__)

_COL_SESSIONS = "sessions"
_COL_CONTROL_MAPPINGS = "controlMappings"
_COL_GAP_FINDINGS = "gapFindings"
_COL_TRANSCRIPT = "transcript"
_COL_OSCAL_OUTPUTS = "oscalOutputs"
_COL_USERS = "users"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class FirestoreService:
    def __init__(self) -> None:
        self._client: AsyncClient | None = None

    def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = firestore.AsyncClient(
                project=settings.google_cloud_project,
                database=settings.firestore_database,
            )
        return self._client

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    async def create_session(self, user_id: str, system_name: str = "") -> str:
        """Create a new assessment session; return session ID."""
        session_id = str(uuid4())
        db = self._get_client()
        await db.collection(_COL_SESSIONS).document(session_id).set({
            "userId": user_id,
            "systemName": system_name,
            "status": "active",
            "conversationPhase": "intake",
            "systemProfile": {},
            "classification": None,
            "createdAt": _utcnow(),
            "updatedAt": _utcnow(),
        })
        logger.info("Created session %s for user %s", session_id, user_id)
        return session_id

    async def get_session(self, session_id: str) -> dict | None:
        db = self._get_client()
        doc = await db.collection(_COL_SESSIONS).document(session_id).get()
        return doc.to_dict() if doc.exists else None

    async def update_session(self, session_id: str, updates: dict[str, Any]) -> None:
        db = self._get_client()
        updates["updatedAt"] = _utcnow()
        await db.collection(_COL_SESSIONS).document(session_id).update(updates)

    async def list_sessions(self, user_id: str, limit: int = 20) -> list[dict]:
        db = self._get_client()
        docs = (
            db.collection(_COL_SESSIONS)
            .where("userId", "==", user_id)
            .order_by("updatedAt", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    async def set_phase(self, session_id: str, phase: str) -> None:
        await self.update_session(session_id, {"conversationPhase": phase})

    async def set_classification(self, session_id: str, classification: dict) -> None:
        await self.update_session(session_id, {"classification": classification})

    async def set_system_profile(self, session_id: str, profile: dict) -> None:
        await self.update_session(session_id, {"systemProfile": profile})

    # ------------------------------------------------------------------
    # Control Mappings (subcollection)
    # ------------------------------------------------------------------

    async def upsert_control_mapping(self, session_id: str, mapping: dict) -> None:
        db = self._get_client()
        control_id = mapping.get("control_id", str(uuid4()))
        mapping["updatedAt"] = _utcnow()
        await (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_CONTROL_MAPPINGS)
            .document(control_id)
            .set(mapping, merge=True)
        )

    async def get_control_mappings(self, session_id: str) -> list[dict]:
        db = self._get_client()
        docs = (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_CONTROL_MAPPINGS)
            .stream()
        )
        results = []
        async for doc in docs:
            results.append(doc.to_dict())
        return results

    # ------------------------------------------------------------------
    # Gap Findings (subcollection)
    # ------------------------------------------------------------------

    async def add_gap_finding(self, session_id: str, finding: dict) -> str:
        db = self._get_client()
        finding_id = finding.get("finding_id") or str(uuid4())
        finding["finding_id"] = finding_id
        finding["createdAt"] = _utcnow()
        await (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_GAP_FINDINGS)
            .document(finding_id)
            .set(finding)
        )
        return finding_id

    async def get_gap_findings(self, session_id: str) -> list[dict]:
        db = self._get_client()
        docs = (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_GAP_FINDINGS)
            .stream()
        )
        results = []
        async for doc in docs:
            results.append(doc.to_dict())
        return results

    # ------------------------------------------------------------------
    # Transcript (subcollection)
    # ------------------------------------------------------------------

    async def add_transcript_entry(self, session_id: str, entry: dict) -> None:
        db = self._get_client()
        entry_id = str(uuid4())
        entry["timestamp"] = _utcnow()
        await (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_TRANSCRIPT)
            .document(entry_id)
            .set(entry)
        )

    async def get_transcript(self, session_id: str, limit: int = 50) -> list[dict]:
        db = self._get_client()
        docs = (
            db.collection(_COL_SESSIONS)
            .document(session_id)
            .collection(_COL_TRANSCRIPT)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        results = []
        async for doc in docs:
            results.append(doc.to_dict())
        return list(reversed(results))

    # ------------------------------------------------------------------
    # OSCAL Outputs (top-level collection)
    # ------------------------------------------------------------------

    async def save_oscal_output(self, session_id: str, doc_type: str, gcs_path: str,
                                 validation_status: str = "pending") -> str:
        db = self._get_client()
        output_id = str(uuid4())
        await db.collection(_COL_OSCAL_OUTPUTS).document(output_id).set({
            "sessionId": session_id,
            "type": doc_type,
            "gcsPath": gcs_path,
            "validationStatus": validation_status,
            "createdAt": _utcnow(),
        })
        return output_id

    async def get_oscal_outputs(self, session_id: str) -> list[dict]:
        db = self._get_client()
        docs = (
            db.collection(_COL_OSCAL_OUTPUTS)
            .where("sessionId", "==", session_id)
            .stream()
        )
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results


firestore_service = FirestoreService()
