"""Azure OpenAI provider.

Azure exposes the same chat-completions tool-calling shape as OpenAI but uses
deployment-name routing and its own auth. We reuse :class:`OpenAIProvider`'s
serialization logic and only swap in :class:`AzureOpenAI` as the client.
"""

from __future__ import annotations

import os

from ai_code_agent.providers.base import ProviderError
from ai_code_agent.providers.openai_provider import OpenAIProvider


class AzureOpenAIProvider(OpenAIProvider):
    name = "azure"

    def __init__(
        self,
        *,
        model: str,
        system_prompt: str,
        api_key: str,
        endpoint: str | None = None,
        api_version: str | None = None,
    ):
        # Skip OpenAIProvider's own __init__ — we need a different client.
        # We still want Provider's bookkeeping, so call its parent directly.
        from ai_code_agent.providers.base import Provider

        Provider.__init__(self, model=model, system_prompt=system_prompt)

        endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_version = (
            api_version or os.environ.get("AZURE_OPENAI_API_VERSION") or "2024-08-01-preview"
        )
        if not api_key:
            raise ProviderError("AZURE_OPENAI_API_KEY is not set")
        if not endpoint:
            raise ProviderError(
                "AZURE_OPENAI_ENDPOINT is not set (e.g. https://my-resource.openai.azure.com)"
            )
        try:
            from openai import AzureOpenAI
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'openai' package is required for Azure. "
                "Install with: pip install ai-code-agent-cli[openai]"
            ) from exc
        self._client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )

    def display_name(self) -> str:
        return f"Azure OpenAI ({self.model})"
