"""
Security Audit Logger
Provides structured audit trail for COMPASS security events.

Addresses:
- OWASP LLM06 (Excessive Agency) — every tool invocation is logged
- Agentic accountability     — agent decisions and actions are traceable
- OWASP LLM01 (Prompt Injection) — detected attempts are recorded
- Session access              — create/read/delete events are captured

Audit entries are written to the 'compass.audit' logger so operators can
route them to a SIEM or Cloud Logging with separate sink configuration.
"""
from __future__ import annotations

import json
import logging
import time
from enum import Enum
from typing import Any

audit_logger = logging.getLogger("compass.audit")


class AuditEventType(str, Enum):
    # ── Session lifecycle ────────────────────────────────────────────────────
    SESSION_CREATE = "session.create"
    SESSION_ACCESS = "session.access"
    SESSION_DELETE = "session.delete"

    # ── Agentic / tool actions ────────────────────────────────────────────────
    TOOL_INVOKE    = "tool.invoke"
    TOOL_SUCCESS   = "tool.success"
    TOOL_FAILURE   = "tool.failure"

    # ── LLM interactions ─────────────────────────────────────────────────────
    LLM_REQUEST    = "llm.request"
    LLM_RESPONSE   = "llm.response"

    # ── Security violations ───────────────────────────────────────────────────
    PROMPT_INJECTION_DETECTED = "security.prompt_injection"
    RATE_LIMIT_EXCEEDED       = "security.rate_limit"
    VALIDATION_FAILURE        = "security.validation"
    UNAUTHORIZED_ACCESS       = "security.unauthorized"

    # ── File operations ───────────────────────────────────────────────────────
    FILE_UPLOAD    = "file.upload"
    FILE_DOWNLOAD  = "file.download"

    # ── WebSocket lifecycle ───────────────────────────────────────────────────
    WS_CONNECT     = "ws.connect"
    WS_DISCONNECT  = "ws.disconnect"


def audit_log(
    event_type: AuditEventType,
    session_id: str = "",
    user_id: str = "",
    details: dict[str, Any] | None = None,
    severity: str = "INFO",
) -> None:
    """
    Emit a structured JSON audit log entry.

    Args:
        event_type: Category of the audited event.
        session_id: Associated assessment session (if applicable).
        user_id:    Authenticated user identifier.
        details:    Additional key/value context (tool name, file size, etc.).
        severity:   "INFO", "WARNING", or "ERROR".
    """
    entry: dict[str, Any] = {
        "audit": True,
        "event": event_type.value,
        "ts": time.time(),
        "session_id": session_id or "",
        "user_id": user_id or "anonymous",
        "severity": severity,
    }
    if details:
        entry.update(details)

    log_fn = (
        audit_logger.error   if severity == "ERROR"
        else audit_logger.warning if severity == "WARNING"
        else audit_logger.info
    )
    log_fn(json.dumps(entry))
