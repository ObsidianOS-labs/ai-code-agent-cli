"""Catalog invariants + ``ProviderKeys.api_key_for`` lookups."""

from __future__ import annotations

import pytest

from ai_code_agent.config import (
    DEFAULT_MODELS,
    SUPPORTED_PROVIDERS,
    ProviderKeys,
    load_config,
)
from ai_code_agent.providers.catalog import CATALOG, entries_by_category, get_entry


def test_catalog_has_at_least_30_entries():
    """Sanity check: the catalog covers the headline 30+ providers we advertise."""
    assert len(CATALOG) >= 30


def test_every_supported_provider_resolves():
    for pid in SUPPORTED_PROVIDERS:
        entry = get_entry(pid)
        assert entry.id == pid


def test_get_entry_unknown_raises():
    with pytest.raises(KeyError):
        get_entry("definitely-not-a-real-provider")


def test_openai_compat_entries_have_base_url_and_env_var():
    for entry in CATALOG.values():
        if entry.kind == "openai_compat":
            assert entry.base_url, f"{entry.id} is openai_compat but has no base_url"
            # LM Studio is the one openai_compat with no env var (local).
            if entry.id != "lmstudio":
                assert entry.env_var, f"{entry.id} is openai_compat but has no env_var"
            assert entry.default_model, f"{entry.id} has empty default_model"


def test_env_vars_unique_across_openai_compat_entries():
    seen: dict[str, str] = {}
    for entry in CATALOG.values():
        if entry.kind != "openai_compat" or not entry.env_var:
            continue
        # GITHUB_TOKEN is also used by other tools — that's fine in general,
        # but must not collide *within* the catalog.
        if entry.env_var in seen:
            raise AssertionError(
                f"env var {entry.env_var} reused by {entry.id} (also used by {seen[entry.env_var]})"
            )
        seen[entry.env_var] = entry.id


def test_entries_by_category_covers_full_catalog():
    grouped = entries_by_category()
    flat = [e.id for items in grouped.values() for e in items]
    assert sorted(flat) == sorted(CATALOG.keys())


def test_default_models_includes_every_non_custom_provider():
    for pid in SUPPORTED_PROVIDERS:
        if pid == "custom":
            continue
        assert pid in DEFAULT_MODELS, f"{pid} missing from DEFAULT_MODELS"


def test_provider_keys_api_key_for_uses_env_var(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk-fake")
    cfg = load_config(
        cli_provider="openai",  # avoid blowing up on missing keys for groq
        cli_working_dir=None,
        config_path=None,
    )
    groq = get_entry("groq")
    assert cfg.keys.api_key_for(groq) == "gsk-fake"


def test_provider_keys_api_key_for_legacy_named_fields():
    keys = ProviderKeys(openai="sk-1", anthropic="sk-2", google="g-3")
    assert keys.api_key_for(get_entry("openai")) == "sk-1"
    assert keys.api_key_for(get_entry("anthropic")) == "sk-2"
    assert keys.api_key_for(get_entry("gemini")) == "g-3"


def test_provider_keys_has_key_for_new_providers(monkeypatch: pytest.MonkeyPatch):
    keys = ProviderKeys(extra_api_keys={"GROQ_API_KEY": "gsk-x"})
    assert keys.has_key_for("groq")
    assert not keys.has_key_for("together")  # no TOGETHER_API_KEY set


def test_provider_keys_has_key_for_cloud_auth_kinds():
    """Azure / Vertex / Bedrock rely on cloud SDK credential chains; we
    optimistically report 'has_key_for' = True so the REPL doesn't block on
    a missing-key check before we even invoke the SDK."""
    keys = ProviderKeys()
    assert keys.has_key_for("azure")
    assert keys.has_key_for("vertex_anthropic")
    assert keys.has_key_for("bedrock")


def test_provider_keys_has_key_for_custom_requires_base_url():
    keys = ProviderKeys()
    assert not keys.has_key_for("custom")
    keys.custom_base_url = "https://x.example/v1"
    assert keys.has_key_for("custom")
