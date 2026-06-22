"""Gemini (Google GenAI) LLM provider implementation.

Supports both API-key mode (local dev) and Vertex AI mode (Cloud Run).
The sidecar force_tool_call() uses gemini_model (text/reasoning model).
The chat_with_tools() uses gemini_model as well.
The Live WebSocket still uses gemini_live_model directly in app.py — native
audio is a Gemini-specific feature with no clean cross-provider abstraction.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from google import genai
from google.genai import types

from backend.providers.base import LLMProvider, ToolCall, ToolExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5


class GeminiProvider(LLMProvider):
    """Wraps google-genai (Gemini) for COMPASS tool-calling workflows."""

    def __init__(self, client: genai.Client, model: str) -> None:
        self._client = client
        self._model = model

    # ------------------------------------------------------------------
    # Schema conversion helpers
    # ------------------------------------------------------------------

    def _json_schema_to_genai(self, schema: dict) -> types.Schema:
        """Recursively convert a JSON Schema dict to google-genai Schema."""
        s_type = (schema.get("type") or "string").upper()
        kwargs: dict = {"type": s_type}

        if desc := schema.get("description"):
            kwargs["description"] = desc
        if enum := schema.get("enum"):
            kwargs["enum"] = enum

        if s_type == "OBJECT":
            props = schema.get("properties", {})
            kwargs["properties"] = {
                k: self._json_schema_to_genai(v) for k, v in props.items()
            }
            if req := schema.get("required"):
                kwargs["required"] = req

        if s_type == "ARRAY" and (items := schema.get("items")):
            kwargs["items"] = self._json_schema_to_genai(items)

        return types.Schema(**kwargs)

    def _tool_to_declaration(self, tool: dict) -> types.FunctionDeclaration:
        params_schema = self._json_schema_to_genai(tool["parameters"])
        return types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters=params_schema,
        )

    # ------------------------------------------------------------------
    # Provider interface
    # ------------------------------------------------------------------

    async def force_tool_call(
        self, prompt: str, tools: list[dict], allowed: list[str]
    ) -> list[ToolCall]:
        declarations = [self._tool_to_declaration(t) for t in tools]
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=declarations)],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="ANY",
                        allowed_function_names=allowed,
                    )
                ),
            ),
        )
        calls: list[ToolCall] = []
        for candidate in response.candidates or []:
            for part in (candidate.content.parts or []) if candidate.content else []:
                if hasattr(part, "function_call") and part.function_call:
                    calls.append(
                        ToolCall(
                            name=part.function_call.name,
                            args=dict(part.function_call.args)
                            if part.function_call.args
                            else {},
                        )
                    )
        return calls

    async def chat_with_tools(
        self,
        system_prompt: str,
        history: list[dict],
        tools: list[dict],
        tool_executor: ToolExecutor,
    ) -> tuple[str, list[dict]]:
        declarations = [self._tool_to_declaration(t) for t in tools]
        tool_cfg = types.Tool(function_declarations=declarations)

        contents: list[types.Content] = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        events: list[dict] = []
        reply_parts: list[str] = []

        for _round in range(MAX_TOOL_ROUNDS):
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[tool_cfg],
                ),
            )

            has_tool_call = False
            for candidate in response.candidates or []:
                content_parts = (
                    candidate.content.parts or []
                ) if candidate.content else []
                for part in content_parts:
                    if part.text:
                        reply_parts.append(part.text)
                    if hasattr(part, "function_call") and part.function_call:
                        has_tool_call = True
                        fn_name = part.function_call.name
                        fn_args = (
                            dict(part.function_call.args)
                            if part.function_call.args
                            else {}
                        )
                        logger.info(
                            "GeminiProvider tool: %s(%s)",
                            fn_name,
                            list(fn_args.keys()),
                        )
                        result = await tool_executor(fn_name, fn_args)
                        event = result.pop("_event", None)
                        if event:
                            events.append(event)

                        contents.append(candidate.content)
                        contents.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part(
                                        function_response=types.FunctionResponse(
                                            name=fn_name,
                                            response={"result": result},
                                        )
                                    )
                                ],
                            )
                        )

            if not has_tool_call:
                break

        return "".join(reply_parts), events

    async def simple_generate(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=10),
        )
        return (response.text or "").strip()

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model
