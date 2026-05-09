"""Tests for the REPL slash-command handler — particularly state rollback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ai_code_agent.agent import Agent
from ai_code_agent.cli import _handle_slash
from ai_code_agent.config import Config, ProviderKeys
from ai_code_agent.providers.base import (
    AssistantResponse,
    Message,
    Provider,
    ProviderError,
)


class _FakeProvider(Provider):
    """Minimal provider that succeeds on construction and never calls the LLM."""

    def __init__(self, *, name: str, model: str = "fake-model"):
        Provider.__init__(self, model=model, system_prompt="(test)")
        # ``name`` is normally a class attribute; per-instance override here for tests.
        object.__setattr__(self, "name", name)

    def complete(self, messages: list[Message]) -> AssistantResponse:
        return AssistantResponse(text="ok")


class _FakeUI:
    """Captures messages instead of printing, so tests can assert on them."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    # The following are unused by /provider and /model handlers but kept for safety.
    def show_help(self) -> None: ...
    def show_status(self, **_: Any) -> None: ...
    def warning(self, msg: str) -> None: ...


@pytest.fixture
def agent_and_cfg(tmp_path: Path):
    cfg = Config(
        provider="openai",
        model="gpt-test",
        working_dir=tmp_path,
        keys=ProviderKeys(openai="sk-test", anthropic="sk-test", google="g-test"),
    )
    agent = Agent(provider=_FakeProvider(name="openai", model="gpt-test"), working_dir=tmp_path)
    return agent, cfg


def test_provider_rollback_on_build_failure(monkeypatch, agent_and_cfg):
    """If ``build_provider`` raises after we've mutated ``cfg``, the cfg state
    must be restored so subsequent slash commands keep working."""
    agent, cfg = agent_and_cfg
    ui = _FakeUI()

    def boom(_cfg: Config, *, system_prompt: str) -> Provider:
        raise ProviderError("simulated SDK missing")

    monkeypatch.setattr("ai_code_agent.cli.build_provider", boom)

    stop = _handle_slash(
        "/provider anthropic",
        ui=ui,
        agent=agent,
        cfg=cfg,
        system_prompt="(test)",
    )

    assert stop is False
    assert ui.errors, "expected an error message to be surfaced"
    # State must have been restored.
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-test"
    # Agent must still be on the original provider.
    assert agent.provider.name == "openai"


def test_provider_rollback_on_missing_key(agent_and_cfg):
    agent, cfg = agent_and_cfg
    cfg.keys.anthropic = None  # remove the key for the target provider
    ui = _FakeUI()

    stop = _handle_slash(
        "/provider anthropic",
        ui=ui,
        agent=agent,
        cfg=cfg,
        system_prompt="(test)",
    )

    assert stop is False
    assert any("missing API key" in e for e in ui.errors)
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-test"


def test_provider_switch_succeeds(monkeypatch, agent_and_cfg):
    agent, cfg = agent_and_cfg
    ui = _FakeUI()

    def fake_build(c: Config, *, system_prompt: str) -> Provider:
        return _FakeProvider(name=c.provider, model="new-model")

    monkeypatch.setattr("ai_code_agent.cli.build_provider", fake_build)

    stop = _handle_slash(
        "/provider anthropic",
        ui=ui,
        agent=agent,
        cfg=cfg,
        system_prompt="(test)",
    )

    assert stop is False
    assert ui.errors == []
    assert cfg.provider == "anthropic"
    assert agent.provider.name == "anthropic"


def test_model_rollback_on_build_failure(monkeypatch, agent_and_cfg):
    agent, cfg = agent_and_cfg
    ui = _FakeUI()

    def boom(_cfg: Config, *, system_prompt: str) -> Provider:
        raise ProviderError("simulated bad model")

    monkeypatch.setattr("ai_code_agent.cli.build_provider", boom)

    stop = _handle_slash(
        "/model gpt-bogus",
        ui=ui,
        agent=agent,
        cfg=cfg,
        system_prompt="(test)",
    )

    assert stop is False
    assert ui.errors
    assert cfg.model == "gpt-test"
    assert agent.provider.model == "gpt-test"
