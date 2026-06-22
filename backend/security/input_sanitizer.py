"""
Input Sanitizer
Defends against OWASP LLM01 (Prompt Injection), LLM06 (Excessive Agency),
and Agentic unbounded input risks.

Provides:
- Prompt injection pattern detection (context-update spoofing, jailbreaks)
- Length enforcement per input type
- Control-character stripping
- File upload validation (LLM10 / Agentic resource exhaustion)
- GCS path validation (SSRF prevention)
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Length limits
# ---------------------------------------------------------------------------
MAX_USER_MESSAGE_LEN = 4_000
MAX_SESSION_ID_LEN = 64
MAX_USER_ID_LEN = 128
MAX_TOOL_ARG_LEN = 2_000
MAX_SYSTEM_NAME_LEN = 200
MAX_VECTOR_QUERY_LEN = 500
MAX_DIAGRAM_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_TRANSCRIPT_LIMIT = 100                   # cap the ?limit= query param

# ---------------------------------------------------------------------------
# Prompt injection patterns (LLM01)
# ---------------------------------------------------------------------------
# Each tuple is (pattern, description) for structured logging.
_INJECTION_PATTERNS: list[tuple[str, str]] = [
    # ── Context-update spoofing ──────────────────────────────────────────────
    (r"\[COMPASS\s+CONTEXT\s+UPDATE\]", "context_update_spoof"),
    # ── Classic instruction-override jailbreaks ──────────────────────────────
    (r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "ignore_instructions"),
    (r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "disregard_instructions"),
    (r"forget\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "forget_instructions"),
    (r"override\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", "override_instructions"),
    (r"you\s+are\s+now\s+(?:in\s+)?(?:developer|god|unrestricted|jailbreak)\s+mode", "mode_switch"),
    (r"new\s+system\s+(?:prompt|instruction)", "new_system_prompt"),
    (r"act\s+as\s+(?:an?\s+)?(?:unrestricted|uncensored|evil|different)\s+(?:AI|assistant|model)", "act_as"),
    (r"\bDAN\s+mode\b", "dan_mode"),
    (r"\bjailbreak\b", "jailbreak_keyword"),
    # ── System prompt extraction (LLM07) ────────────────────────────────────
    (r"(?:reveal|show|print|repeat|output|write\s+out)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
    (r"what\s+(?:are|is)\s+(?:your|the)\s+(?:full\s+)?(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
    (r"(?:display|expose|dump)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
    # ── Role/persona manipulation ────────────────────────────────────────────
    (r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a\s+)?(?:different|another|evil|uncensored)", "role_manipulation"),
    (r"roleplay\s+as\s+(?:an?\s+)?(?:unrestricted|evil|different|hacker)", "roleplay_abuse"),
]

_COMPILED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE), desc)
    for pat, desc in _INJECTION_PATTERNS
]

# Control characters except \t (0x09) and \n (0x0a) and \r (0x0d)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Allowed GCS bucket prefix for diagrams and OSCAL (SSRF guard)
_ALLOWED_GCS_BUCKET_RE = re.compile(r"^gs://compass-hackathon-oscal/sessions/[a-f0-9\-]{36}/")


class InputValidationError(ValueError):
    """Raised when user input fails validation checks."""
    pass


# ---------------------------------------------------------------------------
# Public sanitization functions
# ---------------------------------------------------------------------------

def sanitize_user_message(text: str) -> str:
    """
    Validate and sanitize a free-text user message before it is embedded in
    any LLM prompt.

    Steps:
    1. Type check
    2. Strip null bytes and ASCII control characters
    3. Enforce MAX_USER_MESSAGE_LEN (truncate with warning)
    4. Scan for prompt injection patterns → raise InputValidationError
    5. Return stripped text

    Raises:
        InputValidationError: if injection patterns are detected.
    """
    if not isinstance(text, str):
        raise InputValidationError("Message must be a string")

    # Strip dangerous control characters
    text = _CONTROL_CHAR_RE.sub("", text)

    # Truncate — log so operators know it happened
    if len(text) > MAX_USER_MESSAGE_LEN:
        logger.warning(
            "User message truncated from %d to %d chars (LLM10 guard)",
            len(text),
            MAX_USER_MESSAGE_LEN,
        )
        text = text[:MAX_USER_MESSAGE_LEN]

    # Detect prompt injection
    for pattern, desc in _COMPILED_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Prompt injection attempt blocked: type=%s pattern=%s",
                desc,
                pattern.pattern[:50],
            )
            raise InputValidationError(
                "Your message contains content that cannot be processed. "
                "Please rephrase your request focusing on your compliance assessment."
            )

    return text.strip()


def sanitize_session_id(session_id: str) -> str:
    """
    Validate a session ID string.
    Accepts UUID-format IDs only (hex digits and hyphens, max 64 chars).

    Raises:
        InputValidationError: if the format is invalid.
    """
    if not isinstance(session_id, str) or not session_id:
        raise InputValidationError("session_id must be a non-empty string")
    if len(session_id) > MAX_SESSION_ID_LEN:
        raise InputValidationError("session_id too long")
    if not re.fullmatch(r"[a-fA-F0-9\-]{8,64}", session_id):
        raise InputValidationError("Invalid session_id format")
    return session_id


def sanitize_user_id(user_id: str) -> str:
    """
    Validate a user ID string.
    Allows alphanumeric, @, ., _, - only.

    Raises:
        InputValidationError: if the format is invalid.
    """
    if not isinstance(user_id, str) or not user_id:
        raise InputValidationError("user_id must be a non-empty string")
    if len(user_id) > MAX_USER_ID_LEN:
        raise InputValidationError("user_id too long")
    if not re.fullmatch(r"[a-zA-Z0-9@._\-]+", user_id):
        raise InputValidationError("Invalid user_id format")
    return user_id


def sanitize_tool_arg(value: str, max_len: int = MAX_TOOL_ARG_LEN) -> str:
    """
    Sanitize a string argument that the LLM has extracted from conversation
    and will pass to a tool implementation.  Control characters are stripped
    and the value is truncated to prevent oversized writes to Firestore / GCS.
    """
    if not isinstance(value, str):
        return str(value)[:max_len]
    value = _CONTROL_CHAR_RE.sub("", value)
    return value[:max_len]


def validate_diagram_upload(data: bytes, content_type: str) -> None:
    """
    Validate a diagram file upload.

    Enforces:
    - MAX_DIAGRAM_SIZE_BYTES file-size cap  (LLM10 / resource exhaustion)
    - Allow-list of image MIME types        (prevent malicious file uploads)

    Raises:
        InputValidationError: on size or type violations.
    """
    if len(data) > MAX_DIAGRAM_SIZE_BYTES:
        raise InputValidationError(
            f"File too large. Maximum diagram size is "
            f"{MAX_DIAGRAM_SIZE_BYTES // (1024 * 1024)} MB."
        )
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
    if content_type not in allowed_types:
        raise InputValidationError(
            f"Unsupported file type '{content_type}'. "
            f"Allowed types: {', '.join(sorted(allowed_types))}"
        )


def validate_gcs_path(gcs_path: str) -> str:
    """
    Validate that a GCS path is within the expected COMPASS bucket
    (prevents SSRF-style GCS path traversal attacks).

    Raises:
        InputValidationError: if the path is outside the allowed bucket prefix.
    """
    if not isinstance(gcs_path, str) or not gcs_path.startswith("gs://"):
        raise InputValidationError("Invalid GCS path format")
    if not _ALLOWED_GCS_BUCKET_RE.match(gcs_path):
        raise InputValidationError("GCS path references an unauthorised location")
    return gcs_path
