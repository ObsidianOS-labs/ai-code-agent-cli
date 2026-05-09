"""Build a concrete :class:`Provider` from a :class:`Config`."""

from __future__ import annotations

from ai_code_agent.config import Config
from ai_code_agent.providers.base import Provider, ProviderError


def build_provider(config: Config, system_prompt: str) -> Provider:
    """Construct the provider for ``config.provider`` using ``config.keys``."""
    provider = config.provider
    model = config.effective_model
    if not model:
        raise ProviderError(f"No model configured for provider {provider!r}")

    if provider == "openai":
        from ai_code_agent.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.openai or "",
        )

    if provider == "anthropic":
        from ai_code_agent.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.anthropic or "",
        )

    if provider == "gemini":
        from ai_code_agent.providers.gemini_provider import GeminiProvider

        return GeminiProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.google or "",
        )

    if provider == "ollama":
        from ai_code_agent.providers.ollama_provider import OllamaProvider

        return OllamaProvider(
            model=model,
            system_prompt=system_prompt,
            base_url=config.keys.ollama_base_url,
        )

    raise ProviderError(f"Unknown provider: {provider}")
