"""Shell and Python-script execution tools."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

from ai_code_agent.safety import resolve_within

OUTPUT_BYTE_LIMIT = 64 * 1024


def run_command(
    working_dir: Path,
    command: str,
    timeout: int = 60,
) -> str:
    """Run ``command`` via ``/bin/sh -c`` (or cmd on Windows) inside ``working_dir``."""
    if not command.strip():
        raise ValueError("Empty command")

    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return _format_output(
            command=command,
            returncode=None,
            stdout=out,
            stderr=err,
            timed_out=True,
            timeout=timeout,
        )

    return _format_output(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def run_python_file(
    working_dir: Path,
    file_path: str,
    args: list[str] | None = None,
    timeout: int = 60,
) -> str:
    """Run a Python file with the current interpreter."""
    target = resolve_within(working_dir, file_path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if target.suffix != ".py":
        raise ValueError(f"Not a .py file: {file_path}")

    args = list(args or [])
    cmd = [sys.executable, str(target), *args]
    pretty = " ".join(shlex.quote(c) for c in cmd)
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return _format_output(
            command=pretty,
            returncode=None,
            stdout=out,
            stderr=err,
            timed_out=True,
            timeout=timeout,
        )

    return _format_output(
        command=pretty,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _format_output(
    *,
    command: str,
    returncode: int | None,
    stdout: str,
    stderr: str,
    timed_out: bool = False,
    timeout: int | None = None,
) -> str:
    parts: list[str] = [f"$ {command}"]
    if timed_out:
        parts.append(f"[timeout after {timeout}s]")
    parts.append(f"[exit {returncode if returncode is not None else 'killed'}]")

    stdout = _truncate(stdout)
    stderr = _truncate(stderr)
    if stdout:
        parts.append("--- stdout ---\n" + stdout.rstrip())
    if stderr:
        parts.append("--- stderr ---\n" + stderr.rstrip())
    if not stdout and not stderr:
        parts.append("(no output)")
    return "\n".join(parts)


def _truncate(text: str, limit: int = OUTPUT_BYTE_LIMIT) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    chopped = encoded[:limit].decode("utf-8", errors="replace")
    return chopped + f"\n... [truncated: {len(encoded)} bytes total, kept first {limit}]"
