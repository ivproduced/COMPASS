"""
COMPASS Security Module
Provides input validation, rate limiting, and audit logging
to harden the application against OWASP LLM Top 10 and Agentic Top 10 threats.
"""
from backend.security.audit_logger import AuditEventType, audit_log
from backend.security.input_sanitizer import (
    InputValidationError,
    sanitize_user_message,
    sanitize_session_id,
    sanitize_user_id,
    sanitize_tool_arg,
    validate_diagram_upload,
    validate_gcs_path,
)
from backend.security.rate_limiter import rate_limiter, RateLimitRule, RATE_LIMIT_RULES

__all__ = [
    "AuditEventType",
    "audit_log",
    "InputValidationError",
    "sanitize_user_message",
    "sanitize_session_id",
    "sanitize_user_id",
    "sanitize_tool_arg",
    "validate_diagram_upload",
    "validate_gcs_path",
    "rate_limiter",
    "RateLimitRule",
    "RATE_LIMIT_RULES",
]
