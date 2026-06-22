"""OpenAI LLM provider implementation.

Uses the openai async client for both sidecar tool-calling (force_tool_call)
and the multi-turn REST chat endpoint (chat_with_tools).

The Live WebSocket audio path remains Gemini-specific and is not handled here.
"""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from backend.providers.base import LLMProvider, ToolCall, ToolExecutor

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


class OpenAIProvider(LLMProvider):
    """Wraps openai AsyncOpenAI for COMPASS tool-calling workflows."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    # ------------------------------------------------------------------
    # Schema conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tool_to_openai(tool: dict) -> dict:
        """Convert a COMPASS tool schema dict to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }

    # ------------------------------------------------------------------
    # Provider interface
    # ------------------------------------------------------------------

    async def force_tool_call(
        self, prompt: str, tools: list[dict], allowed: list[str]
    ) -> list[ToolCall]:
        oai_tools = [
            self._tool_to_openai(t) for t in tools if t["name"] in allowed
        ]
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            tools=oai_tools,
            tool_choice="required",
        )
        calls: list[ToolCall] = []
        for choice in response.choices:
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    calls.append(ToolCall(name=tc.function.name, args=args))
        return calls

    async def chat_with_tools(
        self,
        system_prompt: str,
        history: list[dict],
        tools: list[dict],
        tool_executor: ToolExecutor,
    ) -> tuple[str, list[dict]]:
        oai_tools = [self._tool_to_openai(t) for t in tools]

        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        events: list[dict] = []
        reply_parts: list[str] = []

        for _round in range(MAX_TOOL_ROUNDS):
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=oai_tools,
            )

            choice = response.choices[0]
            msg = choice.message

            # Build assistant message for history
            assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_msg)

            if not msg.tool_calls:
                if msg.content:
                    reply_parts.append(msg.content)
                break

            for tc in msg.tool_calls:
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                logger.info(
                    "OpenAIProvider tool: %s(%s)",
                    tc.function.name,
                    list(fn_args.keys()),
                )
                result = await tool_executor(tc.function.name, fn_args)
                event = result.pop("_event", None)
                if event:
                    events.append(event)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

        return "".join(reply_parts), events

    async def simple_generate(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        return (response.choices[0].message.content or "").strip()

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model
