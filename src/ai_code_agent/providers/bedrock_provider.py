"""Anthropic on AWS Bedrock.

Uses :class:`anthropic.AnthropicBedrock`, which authenticates via the standard
AWS credential chain (env vars, ``~/.aws/credentials``, instance role, etc.).
Same Messages API as the standard Anthropic adapter, so we just swap the
underlying client.
"""

from __future__ import annotations

import os

from ai_code_agent.providers.anthropic_provider import AnthropicProvider
from ai_code_agent.providers.base import Provider, ProviderError


class BedrockAnthropicProvider(AnthropicProvider):
    name = "bedrock"

    def __init__(
        self,
        *,
        model: str,
        system_prompt: str,
        region: str | None = None,
        max_tokens: int = 4096,
    ):
        Provider.__init__(self, model=model, system_prompt=system_prompt)
        self.max_tokens = max_tokens

        region = region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        if not region:
            raise ProviderError("AWS_REGION is not set. Export AWS_REGION (e.g. us-east-1).")
        try:
            from anthropic import AnthropicBedrock
        except ImportError as exc:  # pragma: no cover
            raise ProviderError(
                "The 'anthropic[bedrock]' package is required. "
                "Install with: pip install 'anthropic[bedrock]'"
            ) from exc
        self._client = AnthropicBedrock(aws_region=region)

    def display_name(self) -> str:
        return f"AWS Bedrock ({self.model})"
