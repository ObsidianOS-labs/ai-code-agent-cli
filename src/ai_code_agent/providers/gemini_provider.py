"""Google Gemini provider via the ``google-genai`` SDK."""

from __future__ import annotations

import json
import uuid
from typing import Any

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
    ToolCall,
)


def _strip_default(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively drop unsupported ``default`` keys from a JSON schema."""
    out: dict[str, Any] = {}
    for k, v in schema.items():
        if k == "default":
            continue
        if isinstance(v, dict):
            out[k] = _strip_default(v)
        elif isinstance(v, list):
            out[k] = [_strip_default(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self, *, model: str, system_prompt: str, api_key: str, **kwargs):
        super().__init__(model=model, system_prompt=system_prompt, **kwargs)
        if not api_key:
            raise ProviderError("GOOGLE_API_KEY is not set")
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'google-genai' package is required. Install with: pip install ai-code-agent-cli[gemini]"
            ) from exc
        self._client = genai.Client(api_key=api_key)
        self._types = genai_types

    def _build_tools(self) -> list[Any]:
        decls = [
            self._types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters=_strip_default(t.parameters),
            )
            for t in self.tools
        ]
        return [self._types.Tool(function_declarations=decls)]

    def _serialize_contents(self, messages: list[Message]) -> list[Any]:
        types = self._types
        contents: list[Any] = []
        i = 0
        # We need a mapping from our tool_call id -> name for tool_response blocks
        id_to_name: dict[str, str] = {}
        while i < len(messages):
            m = messages[i]
            if m.role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=m.content)])
                )
                i += 1
            elif m.role == "assistant":
                parts: list[Any] = []
                if m.content:
                    parts.append(types.Part.from_text(text=m.content))
                for tc in m.tool_calls:
                    id_to_name[tc.id] = tc.name
                    parts.append(types.Part.from_function_call(name=tc.name, args=tc.arguments))
                contents.append(
                    types.Content(role="model", parts=parts or [types.Part.from_text(text="")])
                )
                i += 1
            elif m.role == "tool":
                parts = []
                while i < len(messages) and messages[i].role == "tool":
                    tm = messages[i]
                    name = id_to_name.get(tm.tool_call_id or "", tm.tool_call_id or "tool")
                    response: dict[str, Any] = (
                        {"error": tm.content} if tm.is_error else {"result": tm.content}
                    )
                    parts.append(types.Part.from_function_response(name=name, response=response))
                    i += 1
                contents.append(types.Content(role="user", parts=parts))
            else:
                raise ProviderError(f"Unknown role for Gemini: {m.role}")
        return contents

    def complete(self, messages: list[Message]) -> AssistantResponse:
        types = self._types
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=self._serialize_contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    tools=self._build_tools(),
                ),
            )
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for candidate in response.candidates or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", None) or []:
                fc = getattr(part, "function_call", None)
                if fc:
                    args_raw = getattr(fc, "args", None) or {}
                    if isinstance(args_raw, str):
                        try:
                            args_raw = json.loads(args_raw)
                        except json.JSONDecodeError:
                            args_raw = {"_raw": args_raw}
                    tool_calls.append(
                        ToolCall(
                            id=str(uuid.uuid4()),
                            name=getattr(fc, "name", "") or "",
                            arguments=dict(args_raw or {}),
                        )
                    )
                else:
                    text = getattr(part, "text", None)
                    if text:
                        text_parts.append(text)
            break  # only the first candidate is needed

        return AssistantResponse(
            text="\n".join(text_parts).strip(), tool_calls=tool_calls, raw=response
        )
