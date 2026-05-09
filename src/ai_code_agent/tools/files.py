"""File-listing, reading and writing tools (sandbox-rooted)."""

from __future__ import annotations

from pathlib import Path

from ai_code_agent.safety import relative_display, resolve_within

MAX_READ_BYTES_DEFAULT = 64 * 1024
DIR_LIST_LIMIT = 500


def get_files_info(working_dir: Path, directory: str = ".") -> str:
    """List entries inside ``directory`` with sizes."""
    target = resolve_within(working_dir, directory)
    if not target.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    entries = sorted(
        target.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower()),
    )

    lines: list[str] = [f"# Listing of {relative_display(working_dir, target) or '.'}"]
    if not entries:
        lines.append("(empty)")
        return "\n".join(lines)

    truncated = False
    if len(entries) > DIR_LIST_LIMIT:
        entries = entries[:DIR_LIST_LIMIT]
        truncated = True

    for entry in entries:
        if entry.is_symlink():
            kind = "link"
            size = 0
        elif entry.is_dir():
            kind = "dir "
            size = 0
        else:
            kind = "file"
            try:
                size = entry.stat().st_size
            except OSError:
                size = 0
        lines.append(f"{kind}  {size:>10}  {entry.name}")

    if truncated:
        lines.append(f"... (truncated to {DIR_LIST_LIMIT} entries)")
    return "\n".join(lines)


def get_file_content(
    working_dir: Path,
    file_path: str,
    max_bytes: int = MAX_READ_BYTES_DEFAULT,
) -> str:
    """Read a UTF-8 text file, truncating to ``max_bytes``."""
    target = resolve_within(working_dir, file_path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if target.is_dir():
        raise IsADirectoryError(f"Is a directory, not a file: {file_path}")

    raw = target.read_bytes()
    truncated = len(raw) > max_bytes
    payload = raw[:max_bytes]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("utf-8", errors="replace")
    if truncated:
        text += f"\n\n... [truncated: showed first {max_bytes} bytes of {len(raw)} total bytes]"
    return text


def write_file(working_dir: Path, file_path: str, content: str) -> str:
    """Create or overwrite ``file_path`` with ``content``."""
    target = resolve_within(working_dir, file_path)
    if target.is_dir():
        raise IsADirectoryError(f"Refusing to overwrite a directory: {file_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    rel = relative_display(working_dir, target)
    return f"Wrote {len(content)} chars to {rel}"
