"""Provider-agnostic LLM interface for COMPASS.

Any concrete provider must implement:
  - force_tool_call(): single-round forced function call (used by sidecar)
  - chat_with_tools(): multi-turn agentic chat with tool execution
  - simple_generate(): plain text generation (used for health checks)

Tool schemas use the JSON Schema object format (compatible with OpenAI directly;
Gemini provider converts them to google-genai types internally):

    {
        "name": "classify_system",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {
                "data_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "...",
                }
            },
            "required": ["data_types"],
        },
    }
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass
class ToolCall:
    name: str
    args: dict


ToolExecutor = Callable[[str, dict], Awaitable[dict]]


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------

    @abstractmethod
    async def force_tool_call(
        self,
        prompt: str,
        tools: list[dict],
        allowed: list[str],
    ) -> list[ToolCall]:
        """Single round, force the model to call one of the allowed tools.

        Args:
            prompt: Instruction string (no conversation history needed).
            tools: List of tool schema dicts (JSON Schema / OpenAI format).
            allowed: Subset of tool names the model must choose from.

        Returns:
            List of ToolCall objects (usually exactly one).
        """
        ...

    @abstractmethod
    async def chat_with_tools(
        self,
        system_prompt: str,
        history: list[dict],
        tools: list[dict],
        tool_executor: ToolExecutor,
    ) -> tuple[str, list[dict]]:
        """Multi-turn agentic chat loop with tool execution.

        The provider runs the conversation until the model produces a final
        text response with no more tool calls (up to MAX_TOOL_ROUNDS).

        Args:
            system_prompt: System/persona instruction.
            history: Conversation so far as [{role, content}] dicts.
                     role must be "user" or "assistant".
            tools: List of tool schema dicts.
            tool_executor: Async callable (name, args) → result dict.
                           The caller is responsible for persisting results;
                           results may contain a "_event" key that will be
                           popped and collected into the events list.

        Returns:
            (reply_text, events) where events is a list of structured
            event dicts collected from tool result "_event" keys.
        """
        ...

    @abstractmethod
    async def simple_generate(self, prompt: str) -> str:
        """Single-turn text generation — no tools, no history."""
        ...

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name, e.g. 'gemini' or 'openai'."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier used for inference."""
        ...
