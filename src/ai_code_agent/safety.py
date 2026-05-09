"""Path safety helpers.

Every filesystem-touching tool resolves user-supplied paths through
``resolve_within`` to guarantee they stay inside the agent's working
directory. This blocks both traversal (``../../etc``) and absolute
paths to sensitive locations.
"""

from __future__ import annotations

from pathlib import Path


class PathEscapeError(ValueError):
    """Raised when a path resolves outside the working directory."""


def resolve_within(working_dir: Path, user_path: str | Path) -> Path:
    """Resolve ``user_path`` and verify it stays inside ``working_dir``.

    Args:
        working_dir: Absolute path to the sandbox root.
        user_path: A path supplied by the model (or user). Treated as
            relative to ``working_dir`` unless absolute.

    Returns:
        The fully-resolved absolute path.

    Raises:
        PathEscapeError: If the resolved path is not a descendant of
            ``working_dir``.
    """
    working_dir = working_dir.resolve()
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = working_dir / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(working_dir)
    except ValueError as exc:
        raise PathEscapeError(
            f"Path {user_path!r} resolves to {resolved}, which is outside the "
            f"working directory {working_dir}."
        ) from exc
    return resolved


def relative_display(working_dir: Path, path: Path) -> str:
    """Return ``path`` as a string relative to ``working_dir`` when possible."""
    working_dir = working_dir.resolve()
    path = path.resolve()
    try:
        rel = path.relative_to(working_dir)
        return str(rel) if str(rel) != "." else "."
    except ValueError:
        return str(path)
