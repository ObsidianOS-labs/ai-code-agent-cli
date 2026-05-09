"""Generic OpenAI-compatible provider.

Most third-party LLM hosts speak OpenAI's Chat Completions API at a custom
``base_url``. This adapter is a thin subclass of :class:`OpenAIProvider` that
just records a different ``name``/``display_name`` so the UI shows the right
label and ``/status`` reports the configured provider.
"""

from __future__ import annotations

from ai_code_agent.providers.openai_provider import OpenAIProvider


class OpenAICompatibleProvider(OpenAIProvider):
    name = "openai_compat"
    _display_name: str | None = None

    def __init__(
        self,
        *,
        provider_id: str,
        display_name: str,
        model: str,
        system_prompt: str,
        api_key: str,
        base_url: str,
    ):
        super().__init__(
            model=model,
            system_prompt=system_prompt,
            api_key=api_key,
            base_url=base_url,
        )
        # Per-instance overrides.
        object.__setattr__(self, "name", provider_id)
        self._display_name = display_name

    def display_name(self) -> str:
        if self._display_name:
            return f"{self._display_name} ({self.model})"
        return super().display_name()
