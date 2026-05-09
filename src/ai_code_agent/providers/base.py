"""Provider-agnostic message / tool-call types and the :class:`Provider` ABC."""

from __future__ import annotations

import abc
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ai_code_agent.tools import TOOL_SCHEMAS, ToolSchema


class ProviderError(RuntimeError):
    """Raised on configuration or transport failures from a provider."""


@dataclass
class ToolCall:
    """A single tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """A single turn in the conversation in a provider-agnostic form.

    Roles:
      - ``user`` — user-supplied text.
      - ``assistant`` — model output, optionally containing ``tool_calls``.
      - ``tool`` — the result of a tool invocation; carries
        ``tool_call_id`` and ``content``.
    """

    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    is_error: bool = False


@dataclass
class AssistantResponse:
    """Normalized assistant turn returned by a provider."""

    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any | None = None  # provider-specific original response, for debugging


class Provider(abc.ABC):
    """Base class every concrete provider implements."""

    name: str = "base"

    def __init__(
        self, *, model: str, system_prompt: str, tools: Iterable[ToolSchema] | None = None
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools: list[ToolSchema] = list(tools or TOOL_SCHEMAS)

    @abc.abstractmethod
    def complete(self, messages: list[Message]) -> AssistantResponse:
        """Send ``messages`` and return the assistant turn."""

    def display_name(self) -> str:
        return f"{self.name}:{self.model}"
