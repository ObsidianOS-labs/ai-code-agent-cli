"""Bundled prompt templates for the agent."""

from __future__ import annotations

from importlib.resources import files


def load_system_prompt() -> str:
    """Return the bundled CodeAgent system prompt."""
    return (files(__package__) / "system.md").read_text(encoding="utf-8")
