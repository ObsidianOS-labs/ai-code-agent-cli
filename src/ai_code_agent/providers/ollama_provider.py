"""Ollama provider — uses the local ``/api/chat`` endpoint with tool calling.

Tool-call support requires Ollama 0.3+ and a tool-capable model
(e.g. ``llama3.1``, ``qwen2.5``, ``mistral-nemo``).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
    ToolCall,
)

DEFAULT_TIMEOUT = httpx.Timeout(120.0, read=300.0)


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(
        self, *, model: str, system_prompt: str, base_url: str = "http://localhost:11434", **kwargs
    ):
        super().__init__(model=model, system_prompt=system_prompt, **kwargs)
        self.base_url = base_url.rstrip("/")

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
                payload: dict[str, Any] = {"role": "assistant", "content": m.content or ""}
                if m.tool_calls:
                    payload["tool_calls"] = [
                        {
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments,
                            }
                        }
                        for tc in m.tool_calls
                    ]
                out.append(payload)
            elif m.role == "tool":
                out.append({"role": "tool", "content": m.content})
            else:
                raise ProviderError(f"Unknown role for Ollama: {m.role}")
        return out

    def complete(self, messages: list[Message]) -> AssistantResponse:
        body = {
            "model": self.model,
            "messages": self._serialize_messages(messages),
            "tools": self._serialize_tools(),
            "stream": False,
        }
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.post(f"{self.base_url}/api/chat", json=body)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"Ollama returned HTTP {response.status_code}: {response.text[:500]}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Ollama returned non-JSON: {response.text[:500]}") from exc

        msg = data.get("message", {}) or {}
        text = msg.get("content", "") or ""
        tool_calls: list[ToolCall] = []
        for tc in msg.get("tool_calls", []) or []:
            fn = tc.get("function", {}) or {}
            args = fn.get("arguments", {}) or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id") or str(uuid.uuid4()),
                    name=fn.get("name", ""),
                    arguments=dict(args or {}),
                )
            )
        return AssistantResponse(text=text, tool_calls=tool_calls, raw=data)
