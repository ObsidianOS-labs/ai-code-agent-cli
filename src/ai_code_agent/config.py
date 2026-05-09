"""Runtime configuration: load from env vars, optional ``.env``, and TOML.

Precedence (highest first):
  1. CLI flags / arguments (handled by ``cli.py``)
  2. Environment variables (after loading ``.env`` if present)
  3. ``~/.config/ai-code-agent/config.toml``
  4. Built-in defaults
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover — exercised only on 3.10 runtimes
    import tomli as tomllib  # type: ignore[no-redef]

from dotenv import load_dotenv

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "gemini": "gemini-1.5-flash",
    "ollama": "llama3.1",
}

SUPPORTED_PROVIDERS = tuple(DEFAULT_MODELS.keys())


@dataclass
class ProviderKeys:
    openai: str | None = None
    anthropic: str | None = None
    google: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    def has_key_for(self, provider: str) -> bool:
        if provider == "openai":
            return bool(self.openai)
        if provider == "anthropic":
            return bool(self.anthropic)
        if provider == "gemini":
            return bool(self.google)
        return provider == "ollama"


@dataclass
class Config:
    provider: str = "openai"
    model: str | None = None
    working_dir: Path = field(default_factory=Path.cwd)
    keys: ProviderKeys = field(default_factory=ProviderKeys)
    max_tool_iterations: int = 25
    command_timeout_seconds: int = 60
    config_path: Path | None = None

    @property
    def effective_model(self) -> str:
        return self.model or DEFAULT_MODELS.get(self.provider, "")

    def ensure_provider_supported(self) -> None:
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider {self.provider!r}. "
                f"Choose one of: {', '.join(SUPPORTED_PROVIDERS)}."
            )


def default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ai-code-agent" / "config.toml"


def load_config(
    *,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_working_dir: Path | None = None,
    config_path: Path | None = None,
) -> Config:
    """Resolve the effective :class:`Config` for this run."""
    load_dotenv(override=False)

    cfg_path = config_path or default_config_path()
    file_data: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            with cfg_path.open("rb") as fh:
                file_data = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError):
            file_data = {}

    provider = (
        (
            cli_provider
            or os.environ.get("AI_CODE_AGENT_PROVIDER")
            or file_data.get("provider")
            or "openai"
        )
        .strip()
        .lower()
    )

    model = cli_model or os.environ.get("AI_CODE_AGENT_MODEL") or file_data.get("model") or None

    working_dir = (
        (cli_working_dir or Path(file_data.get("working_dir", Path.cwd()))).expanduser().resolve()
    )
    if not working_dir.exists():
        raise FileNotFoundError(f"Working directory does not exist: {working_dir}")
    if not working_dir.is_dir():
        raise NotADirectoryError(f"Working directory is not a directory: {working_dir}")

    keys = ProviderKeys(
        openai=os.environ.get("OPENAI_API_KEY") or file_data.get("openai_api_key"),
        anthropic=os.environ.get("ANTHROPIC_API_KEY") or file_data.get("anthropic_api_key"),
        google=(
            os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or file_data.get("google_api_key")
        ),
        ollama_base_url=(
            os.environ.get("OLLAMA_BASE_URL")
            or file_data.get("ollama_base_url")
            or "http://localhost:11434"
        ),
    )

    cfg = Config(
        provider=provider,
        model=model,
        working_dir=working_dir,
        keys=keys,
        max_tool_iterations=int(file_data.get("max_tool_iterations", 25)),
        command_timeout_seconds=int(file_data.get("command_timeout_seconds", 60)),
        config_path=cfg_path,
    )
    cfg.ensure_provider_supported()
    return cfg
