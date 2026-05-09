"""Integration test for the agent loop using a fake provider.

The fake provider scripts a sequence of assistant turns so we can verify
that tool results flow back into the model correctly without hitting any
real LLM API.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from ai_code_agent.agent import Agent
from ai_code_agent.providers.base import AssistantResponse, Message, Provider, ToolCall


@dataclass
class _ScriptedProvider(Provider):
    name: str = "scripted"

    def __init__(self, *, responses: list[AssistantResponse]):
        # Call the base init with the bare minimum.
        Provider.__init__(self, model="test", system_prompt="(test)")
        self._queue: list[AssistantResponse] = list(responses)
        self.calls_received: list[list[Message]] = []

    def complete(self, messages: list[Message]) -> AssistantResponse:
        self.calls_received.append([Message(**m.__dict__) for m in messages])
        if not self._queue:
            return AssistantResponse(text="(done)")
        return self._queue.pop(0)


def test_agent_runs_tool_call_then_finishes(tmp_path: Path):
    file_path = "result.txt"
    tool_id = "call_1"
    responses = [
        AssistantResponse(
            text="",
            tool_calls=[
                ToolCall(
                    id=tool_id,
                    name="write_file",
                    arguments={"file_path": file_path, "content": "agent-was-here"},
                )
            ],
        ),
        AssistantResponse(text="Wrote the file successfully.", tool_calls=[]),
    ]
    provider = _ScriptedProvider(responses=responses)
    agent = Agent(provider=provider, working_dir=tmp_path)

    final_text = agent.run_turn("please write a file")

    assert (tmp_path / file_path).read_text() == "agent-was-here"
    assert final_text == "Wrote the file successfully."
    assert len(provider.calls_received) == 2

    second_call_messages = provider.calls_received[1]
    roles = [m.role for m in second_call_messages]
    assert roles == ["user", "assistant", "tool"]
    assert second_call_messages[2].tool_call_id == tool_id
    assert "Wrote" in second_call_messages[2].content


def test_agent_stops_on_iteration_limit(tmp_path: Path):
    looping = AssistantResponse(
        text="",
        tool_calls=[
            ToolCall(
                id=str(uuid.uuid4()),
                name="get_files_info",
                arguments={"directory": "."},
            )
        ],
    )
    provider = _ScriptedProvider(responses=[looping] * 50)
    agent = Agent(provider=provider, working_dir=tmp_path, max_iterations=3)

    result = agent.run_turn("loop")
    assert "stopped after 3" in result
    # 1 user + 3 * (assistant + tool) = 7 messages
    assert len(agent.messages) == 1 + 3 * 2


def test_agent_surface_tool_errors(tmp_path: Path):
    responses = [
        AssistantResponse(
            text="",
            tool_calls=[
                ToolCall(
                    id="t1",
                    name="get_file_content",
                    arguments={"file_path": "missing.txt"},
                )
            ],
        ),
        AssistantResponse(text="ok", tool_calls=[]),
    ]
    provider = _ScriptedProvider(responses=responses)
    agent = Agent(provider=provider, working_dir=tmp_path)
    agent.run_turn("read missing")

    tool_msg = next(m for m in agent.messages if m.role == "tool")
    assert tool_msg.is_error
    assert "FileNotFoundError" in tool_msg.content
