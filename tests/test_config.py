from pathlib import Path

import pytest

from ai_code_agent.config import (
    DEFAULT_MODELS,
    SUPPORTED_PROVIDERS,
    load_config,
)


def test_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AI_CODE_AGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AI_CODE_AGENT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfg = load_config(cli_working_dir=tmp_path, config_path=tmp_path / "missing.toml")
    assert cfg.provider == "openai"
    assert cfg.effective_model == DEFAULT_MODELS["openai"]
    assert cfg.working_dir == tmp_path.resolve()
    assert cfg.keys.openai is None


def test_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_CODE_AGENT_PROVIDER", "anthropic")
    monkeypatch.setenv("AI_CODE_AGENT_MODEL", "claude-3-haiku-latest")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    cfg = load_config(cli_working_dir=tmp_path, config_path=tmp_path / "missing.toml")
    assert cfg.provider == "anthropic"
    assert cfg.effective_model == "claude-3-haiku-latest"
    assert cfg.keys.anthropic == "sk-test"


def test_cli_overrides_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_CODE_AGENT_PROVIDER", "anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    cfg = load_config(
        cli_provider="openai",
        cli_working_dir=tmp_path,
        config_path=tmp_path / "missing.toml",
    )
    assert cfg.provider == "openai"


def test_unsupported_provider_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        load_config(
            cli_provider="not-a-real-provider",
            cli_working_dir=tmp_path,
            config_path=tmp_path / "missing.toml",
        )


def test_supported_providers_have_defaults():
    for name in SUPPORTED_PROVIDERS:
        assert name in DEFAULT_MODELS


def test_toml_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AI_CODE_AGENT_PROVIDER", raising=False)
    monkeypatch.delenv("AI_CODE_AGENT_MODEL", raising=False)
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('provider = "gemini"\nmodel = "gemini-1.5-pro"\nmax_tool_iterations = 10\n')
    cfg = load_config(cli_working_dir=tmp_path, config_path=cfg_file)
    assert cfg.provider == "gemini"
    assert cfg.effective_model == "gemini-1.5-pro"
    assert cfg.max_tool_iterations == 10


def test_keys_has_key_for():
    from ai_code_agent.config import ProviderKeys

    keys = ProviderKeys(openai="x", anthropic=None, google=None)
    assert keys.has_key_for("openai")
    assert not keys.has_key_for("anthropic")
    assert not keys.has_key_for("gemini")
    assert keys.has_key_for("ollama")  # always considered available
