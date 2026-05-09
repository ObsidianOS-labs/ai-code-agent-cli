"""Anthropic on Google Vertex AI.

Uses :class:`anthropic.AnthropicVertex`, which authenticates via Google Cloud
Application Default Credentials (``gcloud auth application-default login`` or
a service account). The same Messages API shape as the standard Anthropic
adapter — so we reuse :class:`AnthropicProvider`'s serialization and just
swap the underlying client.
"""

from __future__ import annotations

import os

from ai_code_agent.providers.anthropic_provider import AnthropicProvider
from ai_code_agent.providers.base import Provider, ProviderError


class VertexAnthropicProvider(AnthropicProvider):
    name = "vertex_anthropic"

    def __init__(
        self,
        *,
        model: str,
        system_prompt: str,
        project_id: str | None = None,
        region: str | None = None,
        max_tokens: int = 4096,
    ):
        Provider.__init__(self, model=model, system_prompt=system_prompt)
        self.max_tokens = max_tokens

        project_id = (
            project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        )
        region = (
            region
            or os.environ.get("CLOUD_ML_REGION")
            or os.environ.get("VERTEX_REGION")
            or "us-east5"
        )
        if not project_id:
            raise ProviderError(
                "GOOGLE_CLOUD_PROJECT is not set. "
                "Run `gcloud config set project <id>` or export the variable."
            )
        try:
            from anthropic import AnthropicVertex
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'anthropic[vertex]' package is required. "
                "Install with: pip install 'anthropic[vertex]'"
            ) from exc
        self._client = AnthropicVertex(project_id=project_id, region=region)

    def display_name(self) -> str:
        return f"Anthropic on Vertex ({self.model})"
