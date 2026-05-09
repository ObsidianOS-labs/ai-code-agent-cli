"""Provider catalog — the single source of truth for every supported provider.

Most providers expose the OpenAI Chat Completions API at a custom ``base_url``
so a single :class:`OpenAICompatibleProvider` (a thin subclass of
:class:`OpenAIProvider`) handles all of them. A few providers have native APIs
that don't fit the OpenAI shape and get their own adapter:

* ``openai``         — OpenAI's own API (the canonical implementation)
* ``anthropic``      — Anthropic's Messages API
* ``gemini``         — Google AI Studio (Gemini)
* ``ollama``         — local Ollama server (no API key required)
* ``azure``          — Azure OpenAI (different auth + deployment routing)
* ``vertex_anthropic`` — Anthropic on Google Vertex (gcloud ADC auth)
* ``bedrock``        — Anthropic / Mistral on AWS Bedrock (SigV4 auth)

For anything not in this catalog, use ``--provider custom --base-url ...
--model ...`` with an env var of your choice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ProviderKind = Literal[
    "openai",
    "openai_compat",
    "anthropic",
    "gemini",
    "ollama",
    "azure",
    "vertex_anthropic",
    "bedrock",
    "custom",
]


@dataclass(frozen=True)
class ProviderEntry:
    """One entry in the provider catalog.

    Attributes:
        id: Short canonical identifier used on the CLI (``--provider <id>``).
        display_name: Human-readable name shown in the UI.
        kind: Implementation strategy — see module docstring.
        default_model: Default model when ``--model`` is not provided.
        env_var: Environment variable that holds the API key. ``None`` means
            no key is needed (Ollama) or the auth is handled out-of-band
            (Vertex/Bedrock/Azure).
        base_url: For ``openai_compat`` providers, the OpenAI-compatible
            endpoint URL. Ignored for other kinds.
        category: Grouping label for the ``providers`` listing.
        docs_url: Optional link to provider docs.
        notes: Optional one-line note shown in ``ai-code-agent providers``.
        extras: pip extras names that must be installed for the provider to
            work (e.g. ``("openai",)``).
    """

    id: str
    display_name: str
    kind: ProviderKind
    default_model: str
    env_var: str | None = None
    base_url: str | None = None
    category: str = "Other"
    docs_url: str | None = None
    notes: str | None = None
    extras: tuple[str, ...] = field(default_factory=tuple)


# ── Catalog ─────────────────────────────────────────────────────────────────
# Entries are intentionally conservative: each one has a URL/model/env_var I'm
# confident about. For providers not yet in the catalog, use the ``custom``
# preset (see bottom of this file) to plug in any OpenAI-compatible endpoint.

_ENTRIES: tuple[ProviderEntry, ...] = (
    # ── Native APIs ────────────────────────────────────────────────────────
    ProviderEntry(
        id="openai",
        display_name="OpenAI",
        kind="openai",
        default_model="gpt-4o-mini",
        env_var="OPENAI_API_KEY",
        category="Native",
        docs_url="https://platform.openai.com/docs",
        extras=("openai",),
    ),
    ProviderEntry(
        id="anthropic",
        display_name="Anthropic",
        kind="anthropic",
        default_model="claude-3-5-sonnet-latest",
        env_var="ANTHROPIC_API_KEY",
        category="Native",
        docs_url="https://docs.anthropic.com",
        extras=("anthropic",),
    ),
    ProviderEntry(
        id="gemini",
        display_name="Google Gemini",
        kind="gemini",
        default_model="gemini-1.5-flash",
        env_var="GOOGLE_API_KEY",
        category="Native",
        docs_url="https://ai.google.dev",
        extras=("gemini",),
    ),
    ProviderEntry(
        id="ollama",
        display_name="Ollama (local)",
        kind="ollama",
        default_model="llama3.1",
        env_var=None,
        category="Local",
        docs_url="https://ollama.com",
        notes="No API key. Set OLLAMA_BASE_URL to override http://localhost:11434.",
    ),
    # ── Cloud-native auth (no public API key) ──────────────────────────────
    ProviderEntry(
        id="azure",
        display_name="Azure OpenAI",
        kind="azure",
        default_model="gpt-4o-mini",
        env_var="AZURE_OPENAI_API_KEY",
        category="Native (cloud auth)",
        docs_url="https://learn.microsoft.com/azure/ai-services/openai",
        notes="Also requires AZURE_OPENAI_ENDPOINT and a deployment name in --model.",
        extras=("openai",),
    ),
    ProviderEntry(
        id="vertex_anthropic",
        display_name="Anthropic on Vertex AI",
        kind="vertex_anthropic",
        default_model="claude-3-5-sonnet-v2@20241022",
        env_var=None,
        category="Native (cloud auth)",
        docs_url="https://docs.anthropic.com/claude/docs/claude-on-vertex-ai",
        notes="Auth via gcloud ADC. Set GOOGLE_CLOUD_PROJECT and CLOUD_ML_REGION.",
        extras=("anthropic-vertex",),
    ),
    ProviderEntry(
        id="bedrock",
        display_name="AWS Bedrock (Anthropic)",
        kind="bedrock",
        default_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        env_var=None,
        category="Native (cloud auth)",
        docs_url="https://docs.aws.amazon.com/bedrock/",
        notes="Auth via standard AWS credential chain. Set AWS_REGION.",
        extras=("anthropic-bedrock",),
    ),
    # ── OpenAI-compatible: top-tier hosted ─────────────────────────────────
    ProviderEntry(
        id="groq",
        display_name="Groq",
        kind="openai_compat",
        default_model="llama-3.3-70b-versatile",
        env_var="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        category="OpenAI-compatible",
        docs_url="https://console.groq.com/docs",
        extras=("openai",),
    ),
    ProviderEntry(
        id="together",
        display_name="Together AI",
        kind="openai_compat",
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        env_var="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.together.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="deepseek",
        display_name="DeepSeek",
        kind="openai_compat",
        default_model="deepseek-chat",
        env_var="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
        category="OpenAI-compatible",
        docs_url="https://api-docs.deepseek.com",
        extras=("openai",),
    ),
    ProviderEntry(
        id="mistral",
        display_name="Mistral",
        kind="openai_compat",
        default_model="mistral-large-latest",
        env_var="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.mistral.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="openrouter",
        display_name="OpenRouter",
        kind="openai_compat",
        default_model="openai/gpt-4o-mini",
        env_var="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        category="Gateway",
        docs_url="https://openrouter.ai/docs",
        notes="Aggregates 100+ models. Use 'vendor/model' format for --model.",
        extras=("openai",),
    ),
    ProviderEntry(
        id="fireworks",
        display_name="Fireworks AI",
        kind="openai_compat",
        default_model="accounts/fireworks/models/llama-v3p3-70b-instruct",
        env_var="FIREWORKS_API_KEY",
        base_url="https://api.fireworks.ai/inference/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.fireworks.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="perplexity",
        display_name="Perplexity",
        kind="openai_compat",
        default_model="sonar",
        env_var="PERPLEXITY_API_KEY",
        base_url="https://api.perplexity.ai",
        category="OpenAI-compatible",
        docs_url="https://docs.perplexity.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="xai",
        display_name="xAI (Grok)",
        kind="openai_compat",
        default_model="grok-2-latest",
        env_var="XAI_API_KEY",
        base_url="https://api.x.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.x.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="cerebras",
        display_name="Cerebras",
        kind="openai_compat",
        default_model="llama-3.3-70b",
        env_var="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://inference-docs.cerebras.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="moonshot",
        display_name="Moonshot AI (Kimi)",
        kind="openai_compat",
        default_model="moonshot-v1-32k",
        env_var="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://platform.moonshot.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="moonshot_cn",
        display_name="Moonshot AI (China)",
        kind="openai_compat",
        default_model="moonshot-v1-32k",
        env_var="MOONSHOT_CN_API_KEY",
        base_url="https://api.moonshot.cn/v1",
        category="OpenAI-compatible (China)",
        extras=("openai",),
    ),
    ProviderEntry(
        id="deepinfra",
        display_name="Deep Infra",
        kind="openai_compat",
        default_model="meta-llama/Llama-3.3-70B-Instruct",
        env_var="DEEPINFRA_API_KEY",
        base_url="https://api.deepinfra.com/v1/openai",
        category="OpenAI-compatible",
        docs_url="https://deepinfra.com/docs",
        extras=("openai",),
    ),
    ProviderEntry(
        id="nvidia",
        display_name="Nvidia NIM",
        kind="openai_compat",
        default_model="meta/llama-3.3-70b-instruct",
        env_var="NVIDIA_API_KEY",
        base_url="https://integrate.api.nvidia.com/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.nvidia.com/nim",
        extras=("openai",),
    ),
    ProviderEntry(
        id="huggingface",
        display_name="Hugging Face",
        kind="openai_compat",
        default_model="meta-llama/Llama-3.3-70B-Instruct",
        env_var="HF_TOKEN",
        base_url="https://router.huggingface.co/v1",
        category="OpenAI-compatible",
        docs_url="https://huggingface.co/docs/inference-providers",
        extras=("openai",),
    ),
    ProviderEntry(
        id="nebius",
        display_name="Nebius Token Factory",
        kind="openai_compat",
        default_model="meta-llama/Llama-3.3-70B-Instruct",
        env_var="NEBIUS_API_KEY",
        base_url="https://api.studio.nebius.com/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.nebius.com/studio/inference",
        extras=("openai",),
    ),
    ProviderEntry(
        id="novita",
        display_name="NovitaAI",
        kind="openai_compat",
        default_model="meta-llama/llama-3.3-70b-instruct",
        env_var="NOVITA_API_KEY",
        base_url="https://api.novita.ai/v3/openai",
        category="OpenAI-compatible",
        docs_url="https://novita.ai/docs",
        extras=("openai",),
    ),
    ProviderEntry(
        id="siliconflow",
        display_name="SiliconFlow",
        kind="openai_compat",
        default_model="deepseek-ai/DeepSeek-V3",
        env_var="SILICONFLOW_API_KEY",
        base_url="https://api.siliconflow.com/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.siliconflow.com",
        extras=("openai",),
    ),
    ProviderEntry(
        id="siliconflow_cn",
        display_name="SiliconFlow (China)",
        kind="openai_compat",
        default_model="deepseek-ai/DeepSeek-V3",
        env_var="SILICONFLOW_CN_API_KEY",
        base_url="https://api.siliconflow.cn/v1",
        category="OpenAI-compatible (China)",
        extras=("openai",),
    ),
    ProviderEntry(
        id="zhipu",
        display_name="Zhipu AI (BigModel)",
        kind="openai_compat",
        default_model="glm-4-plus",
        env_var="ZHIPU_API_KEY",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        category="OpenAI-compatible (China)",
        docs_url="https://bigmodel.cn",
        extras=("openai",),
    ),
    ProviderEntry(
        id="zai",
        display_name="Z.AI",
        kind="openai_compat",
        default_model="glm-4-plus",
        env_var="ZAI_API_KEY",
        base_url="https://api.z.ai/api/paas/v4",
        category="OpenAI-compatible",
        docs_url="https://docs.z.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="alibaba",
        display_name="Alibaba DashScope",
        kind="openai_compat",
        default_model="qwen-plus",
        env_var="DASHSCOPE_API_KEY",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        category="OpenAI-compatible",
        docs_url="https://www.alibabacloud.com/help/en/model-studio",
        extras=("openai",),
    ),
    ProviderEntry(
        id="alibaba_cn",
        display_name="Alibaba DashScope (China)",
        kind="openai_compat",
        default_model="qwen-plus",
        env_var="DASHSCOPE_CN_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        category="OpenAI-compatible (China)",
        extras=("openai",),
    ),
    ProviderEntry(
        id="modelscope",
        display_name="ModelScope",
        kind="openai_compat",
        default_model="Qwen/QwQ-32B",
        env_var="MODELSCOPE_API_KEY",
        base_url="https://api-inference.modelscope.cn/v1",
        category="OpenAI-compatible (China)",
        docs_url="https://modelscope.cn/docs",
        extras=("openai",),
    ),
    ProviderEntry(
        id="stepfun",
        display_name="StepFun",
        kind="openai_compat",
        default_model="step-1-32k",
        env_var="STEPFUN_API_KEY",
        base_url="https://api.stepfun.com/v1",
        category="OpenAI-compatible (China)",
        docs_url="https://platform.stepfun.com",
        extras=("openai",),
    ),
    ProviderEntry(
        id="minimax",
        display_name="MiniMax (minimax.io)",
        kind="openai_compat",
        default_model="abab6.5s-chat",
        env_var="MINIMAX_API_KEY",
        base_url="https://api.minimax.io/v1",
        category="OpenAI-compatible",
        docs_url="https://www.minimax.io/platform",
        extras=("openai",),
    ),
    ProviderEntry(
        id="minimaxi",
        display_name="MiniMax (minimaxi.com)",
        kind="openai_compat",
        default_model="abab6.5s-chat",
        env_var="MINIMAXI_API_KEY",
        base_url="https://api.minimaxi.com/v1",
        category="OpenAI-compatible (China)",
        extras=("openai",),
    ),
    ProviderEntry(
        id="ovh",
        display_name="OVHcloud AI Endpoints",
        kind="openai_compat",
        default_model="Meta-Llama-3_3-70B-Instruct",
        env_var="OVH_AI_TOKEN",
        base_url="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1",
        category="OpenAI-compatible",
        docs_url="https://endpoints.ai.cloud.ovh.net",
        extras=("openai",),
    ),
    ProviderEntry(
        id="scaleway",
        display_name="Scaleway",
        kind="openai_compat",
        default_model="llama-3.3-70b-instruct",
        env_var="SCALEWAY_API_KEY",
        base_url="https://api.scaleway.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://www.scaleway.com/en/docs/ai-data/managed-inference/",
        extras=("openai",),
    ),
    ProviderEntry(
        id="upstage",
        display_name="Upstage (Solar)",
        kind="openai_compat",
        default_model="solar-pro",
        env_var="UPSTAGE_API_KEY",
        base_url="https://api.upstage.ai/v1/solar",
        category="OpenAI-compatible",
        docs_url="https://developers.upstage.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="poe",
        display_name="Poe",
        kind="openai_compat",
        default_model="GPT-4o-Mini",
        env_var="POE_API_KEY",
        base_url="https://api.poe.com/v1",
        category="Gateway",
        docs_url="https://creator.poe.com/docs/external-application-guide",
        extras=("openai",),
    ),
    ProviderEntry(
        id="venice",
        display_name="Venice AI",
        kind="openai_compat",
        default_model="venice-uncensored",
        env_var="VENICE_API_KEY",
        base_url="https://api.venice.ai/api/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.venice.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="vercel_gateway",
        display_name="Vercel AI Gateway",
        kind="openai_compat",
        default_model="openai/gpt-4o-mini",
        env_var="AI_GATEWAY_API_KEY",
        base_url="https://ai-gateway.vercel.sh/v1",
        category="Gateway",
        docs_url="https://vercel.com/docs/ai-gateway",
        notes="Use 'vendor/model' format for --model.",
        extras=("openai",),
    ),
    ProviderEntry(
        id="github_models",
        display_name="GitHub Models",
        kind="openai_compat",
        default_model="gpt-4o-mini",
        env_var="GITHUB_TOKEN",
        base_url="https://models.github.ai/inference",
        category="OpenAI-compatible",
        docs_url="https://docs.github.com/en/github-models",
        extras=("openai",),
    ),
    ProviderEntry(
        id="cohere",
        display_name="Cohere",
        kind="openai_compat",
        default_model="command-r-plus",
        env_var="COHERE_API_KEY",
        base_url="https://api.cohere.ai/compatibility/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.cohere.com",
        extras=("openai",),
    ),
    ProviderEntry(
        id="lmstudio",
        display_name="LM Studio (local)",
        kind="openai_compat",
        default_model="local-model",
        env_var=None,
        base_url="http://localhost:1234/v1",
        category="Local",
        docs_url="https://lmstudio.ai/docs/local-server",
        notes="Local LM Studio server. No API key required (set LMSTUDIO_API_KEY if you've enabled auth).",
        extras=("openai",),
    ),
    ProviderEntry(
        id="friendli",
        display_name="Friendli",
        kind="openai_compat",
        default_model="meta-llama-3.3-70b-instruct",
        env_var="FRIENDLI_TOKEN",
        base_url="https://inference.friendli.ai/v1",
        category="OpenAI-compatible",
        docs_url="https://docs.friendli.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="302ai",
        display_name="302.AI",
        kind="openai_compat",
        default_model="gpt-4o-mini",
        env_var="AI302_API_KEY",
        base_url="https://api.302.ai/v1",
        category="Gateway",
        docs_url="https://302.ai",
        extras=("openai",),
    ),
    ProviderEntry(
        id="aihubmix",
        display_name="AIHubMix",
        kind="openai_compat",
        default_model="gpt-4o-mini",
        env_var="AIHUBMIX_API_KEY",
        base_url="https://aihubmix.com/v1",
        category="Gateway",
        docs_url="https://aihubmix.com",
        extras=("openai",),
    ),
    # ── Custom (user-supplied) ─────────────────────────────────────────────
    ProviderEntry(
        id="custom",
        display_name="Custom OpenAI-compatible",
        kind="custom",
        default_model="",
        env_var=None,
        category="Custom",
        notes=(
            "For any OpenAI-compatible provider not in the catalog. "
            "Set CUSTOM_OPENAI_BASE_URL, CUSTOM_OPENAI_API_KEY and pass --model."
        ),
        extras=("openai",),
    ),
)

CATALOG: dict[str, ProviderEntry] = {e.id: e for e in _ENTRIES}


def get_entry(provider_id: str) -> ProviderEntry:
    """Return the catalog entry for ``provider_id`` or raise :class:`KeyError`."""
    try:
        return CATALOG[provider_id]
    except KeyError as exc:
        raise KeyError(
            f"Unknown provider {provider_id!r}. "
            f"Run `ai-code-agent providers` to see the full catalog."
        ) from exc


def entries_by_category() -> dict[str, list[ProviderEntry]]:
    """Return catalog entries grouped by category, in catalog order."""
    grouped: dict[str, list[ProviderEntry]] = {}
    for entry in CATALOG.values():
        grouped.setdefault(entry.category, []).append(entry)
    return grouped
