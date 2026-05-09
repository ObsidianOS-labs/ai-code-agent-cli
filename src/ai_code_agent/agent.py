"""The agent loop: prompt the LLM, dispatch tool calls, repeat."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ToolCall,
)
from ai_code_agent.tools import ToolContext, ToolResult, dispatch


class AgentObserver(Protocol):
    """Hooks fired during a single ``Agent.run_turn`` call.

    A UI implementation supplies these to display progress to the user.
    """

    def on_assistant_text(self, text: str) -> None: ...
    def on_tool_call(self, call: ToolCall) -> None: ...
    def on_tool_result(self, call: ToolCall, result: ToolResult) -> None: ...
    def on_iteration_limit(self, limit: int) -> None: ...


@dataclass
class _NullObserver:
    def on_assistant_text(self, text: str) -> None: ...
    def on_tool_call(self, call: ToolCall) -> None: ...
    def on_tool_result(self, call: ToolCall, result: ToolResult) -> None: ...
    def on_iteration_limit(self, limit: int) -> None: ...


@dataclass
class Agent:
    provider: Provider
    working_dir: Path
    max_iterations: int = 25
    messages: list[Message] = field(default_factory=list)
    observer: AgentObserver = field(default_factory=_NullObserver)

    def reset(self) -> None:
        self.messages.clear()

    def run_turn(self, user_input: str) -> str:
        """Send ``user_input`` to the model and process tool calls until done."""
        self.messages.append(Message(role="user", content=user_input))
        ctx = ToolContext(working_dir=self.working_dir)

        final_text = ""
        for _iteration in range(1, self.max_iterations + 1):
            response: AssistantResponse = self.provider.complete(self.messages)

            if response.text:
                self.observer.on_assistant_text(response.text)
                final_text = response.text

            self.messages.append(
                Message(
                    role="assistant",
                    content=response.text,
                    tool_calls=list(response.tool_calls),
                )
            )

            if not response.tool_calls:
                return final_text

            for call in response.tool_calls:
                self.observer.on_tool_call(call)
                result = dispatch(call.name, call.arguments, ctx)
                self.observer.on_tool_result(call, result)
                self.messages.append(
                    Message(
                        role="tool",
                        content=result.output,
                        tool_call_id=call.id,
                        is_error=result.is_error,
                    )
                )

        self.observer.on_iteration_limit(self.max_iterations)
        return final_text or f"[stopped after {self.max_iterations} tool iterations]"
