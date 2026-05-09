"""LLM provider abstraction and concrete implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
    ToolCall,
)

# ``build_provider`` is imported lazily via :func:`__getattr__` to avoid a
# circular import: ``factory`` depends on :mod:`ai_code_agent.config`, which in
# turn imports the provider catalog from this subpackage.
if TYPE_CHECKING:  # pragma: no cover
    from ai_code_agent.providers.factory import build_provider as build_provider

__all__ = [
    "AssistantResponse",
    "Message",
    "Provider",
    "ProviderError",
    "ToolCall",
    "build_provider",
]


def __getattr__(name: str) -> Any:
    if name == "build_provider":
        from ai_code_agent.providers.factory import build_provider as _build

        return _build
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
