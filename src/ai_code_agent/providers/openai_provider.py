"""OpenAI / OpenAI-compatible provider (Chat Completions + tool calling)."""

from __future__ import annotations

import json
from typing import Any

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
    ToolCall,
)


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(
        self, *, model: str, system_prompt: str, api_key: str, base_url: str | None = None, **kwargs
    ):
        super().__init__(model=model, system_prompt=system_prompt, **kwargs)
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'openai' package is required. Install with: pip install ai-code-agent-cli[openai]"
            ) from exc
        self._client = (
            OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        )

    def _serialize_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.tools
        ]

    def _serialize_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]
        for m in messages:
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                payload: dict[str, Any] = {"role": "assistant", "content": m.content or None}
                if m.tool_calls:
                    payload["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in m.tool_calls
                    ]
                out.append(payload)
            elif m.role == "tool":
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": m.tool_call_id or "",
                        "content": m.content,
                    }
                )
            else:
                raise ProviderError(f"Unknown role for OpenAI: {m.role}")
        return out

    def complete(self, messages: list[Message]) -> AssistantResponse:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self._serialize_messages(messages),
                tools=self._serialize_tools(),
                tool_choice="auto",
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        choice = response.choices[0].message
        text = choice.content or ""
        tool_calls: list[ToolCall] = []
        for tc in choice.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
        return AssistantResponse(text=text, tool_calls=tool_calls, raw=response)
