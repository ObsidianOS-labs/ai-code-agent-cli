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

from ai_code_agent.providers.catalog import CATALOG, ProviderEntry, get_entry

# Public surface kept stable for back-compat with earlier code & tests.
DEFAULT_MODELS: dict[str, str] = {
    entry.id: entry.default_model for entry in CATALOG.values() if entry.default_model
}
SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(CATALOG.keys())


@dataclass
class ProviderKeys:
    # Named fields kept for back-compat with the original four providers.
    openai: str | None = None
    anthropic: str | None = None
    google: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Generic env-var → value map populated for every catalog entry that has
    # an ``env_var`` set. ``api_key_for`` reads from here.
    extra_api_keys: dict[str, str] = field(default_factory=dict)

    # For ``--provider custom`` and similar bring-your-own-endpoint flows.
    custom_base_url: str | None = None
    custom_api_key: str | None = None

    def api_key_for(self, entry: ProviderEntry) -> str | None:
        """Return the API key to use for ``entry``, or ``None`` if unknown."""
        # Honour the legacy named fields first so existing flows keep working.
        if entry.id == "openai":
            return self.openai
        if entry.id == "anthropic":
            return self.anthropic
        if entry.id == "gemini":
            return self.google
        if entry.id == "custom":
            return self.custom_api_key
        if entry.env_var:
            return self.extra_api_keys.get(entry.env_var)
        return None

    def has_key_for(self, provider: str) -> bool:
        try:
            entry = get_entry(provider)
        except KeyError:
            return False
        if entry.kind == "ollama":
            return True
        if entry.kind in ("azure", "vertex_anthropic", "bedrock"):
            # These rely on cloud SDK credential chains; we can't verify here
            # without invoking the SDK, so optimistically return True.
            return True
        if entry.kind == "custom":
            return bool(self.custom_base_url)
        if entry.kind == "openai_compat" and not entry.env_var:
            # Local OpenAI-compatible servers (e.g. LM Studio) don't require
            # an API key — the factory passes a placeholder string instead.
            return True
        return bool(self.api_key_for(entry))


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

    def entry(self) -> ProviderEntry:
        return get_entry(self.provider)

    def ensure_provider_supported(self) -> None:
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider {self.provider!r}. "
                f"Run `ai-code-agent providers` to see the full catalog."
            )


def default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ai-code-agent" / "config.toml"


def _load_extra_api_keys() -> dict[str, str]:
    """Read every catalog entry's ``env_var`` from the environment.

    Each value is captured at load time so callers can inspect availability
    without re-reading the environment. Entries with no ``env_var`` (Ollama,
    Vertex, Bedrock, custom) are skipped.
    """
    result: dict[str, str] = {}
    for entry in CATALOG.values():
        if not entry.env_var:
            continue
        value = os.environ.get(entry.env_var)
        if value:
            result[entry.env_var] = value
    return result


def load_config(
    *,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_working_dir: Path | None = None,
    config_path: Path | None = None,
    cli_base_url: str | None = None,
    cli_api_key: str | None = None,
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
        extra_api_keys=_load_extra_api_keys(),
        custom_base_url=(
            cli_base_url
            or os.environ.get("CUSTOM_OPENAI_BASE_URL")
            or file_data.get("custom_base_url")
        ),
        custom_api_key=(
            cli_api_key
            or os.environ.get("CUSTOM_OPENAI_API_KEY")
            or file_data.get("custom_api_key")
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
