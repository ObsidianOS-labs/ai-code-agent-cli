"""Regex search across the working directory."""

from __future__ import annotations

import re
from pathlib import Path

from ai_code_agent.safety import relative_display, resolve_within

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".tox",
    ".idea",
    ".vscode",
}

MAX_FILE_BYTES_FOR_SEARCH = 2 * 1024 * 1024  # 2 MiB


def grep_search(
    working_dir: Path,
    pattern: str,
    directory: str = ".",
    max_results: int = 200,
) -> str:
    """Recursively search ``directory`` for lines matching ``pattern``."""
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid regex {pattern!r}: {exc}") from exc

    root = resolve_within(working_dir, directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    matches: list[str] = []
    truncated = False

    for path in _walk_text_files(root):
        if len(matches) >= max_results:
            truncated = True
            break
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if regex.search(line):
                        rel = relative_display(working_dir, path)
                        snippet = line.rstrip("\n")
                        if len(snippet) > 240:
                            snippet = snippet[:240] + "…"
                        matches.append(f"{rel}:{lineno}:{snippet}")
                        if len(matches) >= max_results:
                            truncated = True
                            break
        except OSError:
            continue

    if not matches:
        return f"No matches for pattern {pattern!r} in {relative_display(working_dir, root) or '.'}"

    header = f"# {len(matches)} match(es) for {pattern!r}"
    if truncated:
        header += f" (truncated to {max_results})"
    return header + "\n" + "\n".join(matches)


def _walk_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES_FOR_SEARCH:
                continue
        except OSError:
            continue
        yield path
