"""Build a concrete :class:`Provider` from a :class:`Config`."""

from __future__ import annotations

import os

from ai_code_agent.config import Config
from ai_code_agent.providers.base import Provider, ProviderError


def build_provider(config: Config, system_prompt: str) -> Provider:
    """Construct the provider for ``config.provider`` using ``config.keys``."""
    entry = config.entry()
    model = config.effective_model
    if not model:
        raise ProviderError(
            f"No model configured for provider {entry.id!r}. "
            f"Pass --model or set AI_CODE_AGENT_MODEL."
        )

    kind = entry.kind

    if kind == "openai":
        from ai_code_agent.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.openai or "",
        )

    if kind == "anthropic":
        from ai_code_agent.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.anthropic or "",
        )

    if kind == "gemini":
        from ai_code_agent.providers.gemini_provider import GeminiProvider

        return GeminiProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=config.keys.google or "",
        )

    if kind == "ollama":
        from ai_code_agent.providers.ollama_provider import OllamaProvider

        return OllamaProvider(
            model=model,
            system_prompt=system_prompt,
            base_url=config.keys.ollama_base_url,
        )

    if kind == "openai_compat":
        from ai_code_agent.providers.openai_compat import OpenAICompatibleProvider

        api_key = config.keys.api_key_for(entry) or ""
        if not api_key and entry.id != "lmstudio":
            raise ProviderError(f"Missing API key for {entry.display_name}: set ${entry.env_var}.")
        if not entry.base_url:
            raise ProviderError(f"Catalog entry {entry.id!r} has no base_url configured.")
        return OpenAICompatibleProvider(
            provider_id=entry.id,
            display_name=entry.display_name,
            model=model,
            system_prompt=system_prompt,
            api_key=api_key or "lmstudio",  # LM Studio accepts any non-empty string
            base_url=entry.base_url,
        )

    if kind == "azure":
        from ai_code_agent.providers.azure_provider import AzureOpenAIProvider

        api_key = config.keys.api_key_for(entry) or ""
        return AzureOpenAIProvider(
            model=model,
            system_prompt=system_prompt,
            api_key=api_key,
        )

    if kind == "vertex_anthropic":
        from ai_code_agent.providers.vertex_anthropic_provider import (
            VertexAnthropicProvider,
        )

        return VertexAnthropicProvider(model=model, system_prompt=system_prompt)

    if kind == "bedrock":
        from ai_code_agent.providers.bedrock_provider import BedrockAnthropicProvider

        return BedrockAnthropicProvider(model=model, system_prompt=system_prompt)

    if kind == "custom":
        from ai_code_agent.providers.openai_compat import OpenAICompatibleProvider

        base_url = config.keys.custom_base_url or os.environ.get("CUSTOM_OPENAI_BASE_URL")
        api_key = config.keys.custom_api_key or os.environ.get("CUSTOM_OPENAI_API_KEY") or ""
        if not base_url:
            raise ProviderError(
                "Custom provider requires CUSTOM_OPENAI_BASE_URL "
                "(or pass --base-url). Example: https://my-llm.example.com/v1"
            )
        return OpenAICompatibleProvider(
            provider_id="custom",
            display_name="Custom OpenAI-compatible",
            model=model,
            system_prompt=system_prompt,
            api_key=api_key or "no-key",
            base_url=base_url,
        )

    raise ProviderError(f"Unknown provider kind {kind!r} for {entry.id!r}")
