"""Anthropic Messages API provider."""

from __future__ import annotations

from typing import Any

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
    ToolCall,
)


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(
        self, *, model: str, system_prompt: str, api_key: str, max_tokens: int = 4096, **kwargs
    ):
        super().__init__(model=model, system_prompt=system_prompt, **kwargs)
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'anthropic' package is required. Install with: pip install ai-code-agent-cli[anthropic]"
            ) from exc
        self._client = Anthropic(api_key=api_key)
        self.max_tokens = max_tokens

    def _serialize_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in self.tools
        ]

    def _serialize_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        i = 0
        while i < len(messages):
            m = messages[i]
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
                i += 1
            elif m.role == "assistant":
                blocks: list[dict[str, Any]] = []
                if m.content:
                    blocks.append({"type": "text", "text": m.content})
                for tc in m.tool_calls:
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                out.append(
                    {"role": "assistant", "content": blocks or [{"type": "text", "text": ""}]}
                )
                i += 1
            elif m.role == "tool":
                # Anthropic packs tool results into a single user turn; group consecutive tool results.
                blocks = []
                while i < len(messages) and messages[i].role == "tool":
                    tm = messages[i]
                    blocks.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tm.tool_call_id or "",
                            "content": tm.content,
                            "is_error": tm.is_error,
                        }
                    )
                    i += 1
                out.append({"role": "user", "content": blocks})
            else:
                raise ProviderError(f"Unknown role for Anthropic: {m.role}")
        return out

    def complete(self, messages: list[Message]) -> AssistantResponse:
        try:
            response = self._client.messages.create(
                model=self.model,
                system=self.system_prompt,
                messages=self._serialize_messages(messages),
                tools=self._serialize_tools(),
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(getattr(block, "text", "") or "")
            elif block_type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=getattr(block, "id", ""),
                        name=getattr(block, "name", ""),
                        arguments=dict(getattr(block, "input", {}) or {}),
                    )
                )
        return AssistantResponse(
            text="\n".join(text_parts).strip(), tool_calls=tool_calls, raw=response
        )
