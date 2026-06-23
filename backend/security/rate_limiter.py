"""
In-Memory Rate Limiter
Defends against OWASP LLM10 (Unbounded Consumption) and Agentic resource exhaustion.

Implements a sliding-window counter per (category, key) pair.

NOTE: This is a single-process in-memory store.  In a multi-replica Cloud Run
deployment, replace this with a Redis-backed distributed limiter (e.g. via
google-cloud-redis or a Memorystore connection).
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitRule:
    max_requests: int
    window_seconds: int


def _build_rate_limit_rules() -> dict[str, RateLimitRule]:
    return {
        "websocket": RateLimitRule(
            max_requests=settings.rate_limit_websocket,
            window_seconds=60,
        ),
        "chat": RateLimitRule(
            max_requests=settings.rate_limit_chat,
            window_seconds=60,
        ),
        "session_create": RateLimitRule(
            max_requests=settings.rate_limit_session_create,
            window_seconds=60,
        ),
        "diagram_upload": RateLimitRule(
            max_requests=settings.rate_limit_diagram_upload,
            window_seconds=60,
        ),
        "default": RateLimitRule(
            max_requests=settings.rate_limit_default,
            window_seconds=60,
        ),
    }


# ---------------------------------------------------------------------------
# Per-category rules
# ---------------------------------------------------------------------------
RATE_LIMIT_RULES: dict[str, RateLimitRule] = _build_rate_limit_rules()


class InMemoryRateLimiter:
    """
    Sliding-window rate limiter backed by in-memory deques.

    Each (category, key) pair maintains an ordered deque of request timestamps.
    On each check, stale timestamps are evicted and the remaining count is
    compared to the rule's max_requests.
    """

    def __init__(self) -> None:
        # _windows[category][key] → deque of monotonic timestamps
        self._windows: dict[str, dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        category: str = "default",
    ) -> tuple[bool, int]:
        """
        Check whether a request identified by *key* is within the rate limit
        for *category*.

        Args:
            key:      Unique request identifier (e.g. client IP or session ID).
            category: Rule category from RATE_LIMIT_RULES.

        Returns:
            (allowed, retry_after_seconds) — if allowed is False the caller
            should return HTTP 429 with the Retry-After header set to
            retry_after_seconds.
        """
        rule = RATE_LIMIT_RULES.get(category) or RATE_LIMIT_RULES["default"]
        async with self._lock:
            now = time.monotonic()
            window = self._windows[category][key]
            cutoff = now - rule.window_seconds

            # Evict timestamps outside the window
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= rule.max_requests:
                retry_after = max(1, int(window[0] - cutoff) + 1)
                logger.warning(
                    "Rate limit exceeded: category=%s key=%.20s (%d/%d in %ds)",
                    category,
                    key,
                    len(window),
                    rule.max_requests,
                    rule.window_seconds,
                )
                return False, retry_after

            window.append(now)
            return True, 0

    async def cleanup_stale_keys(self) -> None:
        """
        Evict stale timestamps and remove empty keys to prevent unbounded memory growth.
        Should be called periodically (e.g. every 5 minutes) by a background task.
        """
        async with self._lock:
            now = time.monotonic()
            for category in list(self._windows):
                rule = RATE_LIMIT_RULES.get(category) or RATE_LIMIT_RULES["default"]
                cutoff = now - rule.window_seconds
                for key in list(self._windows[category]):
                    window = self._windows[category][key]
                    # Evict expired timestamps first
                    while window and window[0] < cutoff:
                        window.popleft()
                    if not window:
                        del self._windows[category][key]
                if not self._windows[category]:
                    del self._windows[category]


# Singleton instance
rate_limiter = InMemoryRateLimiter()
