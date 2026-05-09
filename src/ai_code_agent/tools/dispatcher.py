"""Centralized tool execution.

The agent loop calls :func:`dispatch` with a tool name and arguments. The
dispatcher routes to the concrete implementation, captures errors, and returns
a stable :class:`ToolResult` regardless of provider.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai_code_agent.tools import files as file_tools
from ai_code_agent.tools import search as search_tools
from ai_code_agent.tools import shell as shell_tools


class ToolError(Exception):
    """Raised when a tool fails in a way the model should see."""


@dataclass
class ToolContext:
    working_dir: Path
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    name: str
    output: str
    is_error: bool = False


def _tool_get_files_info(ctx: ToolContext, args: dict[str, Any]) -> str:
    return file_tools.get_files_info(ctx.working_dir, args.get("directory", "."))


def _tool_get_file_content(ctx: ToolContext, args: dict[str, Any]) -> str:
    return file_tools.get_file_content(
        ctx.working_dir,
        args["file_path"],
        max_bytes=int(args.get("max_bytes", file_tools.MAX_READ_BYTES_DEFAULT)),
    )


def _tool_grep_search(ctx: ToolContext, args: dict[str, Any]) -> str:
    return search_tools.grep_search(
        ctx.working_dir,
        pattern=args["pattern"],
        directory=args.get("directory", "."),
        max_results=int(args.get("max_results", 200)),
    )


def _tool_write_file(ctx: ToolContext, args: dict[str, Any]) -> str:
    return file_tools.write_file(ctx.working_dir, args["file_path"], args["content"])


def _tool_run_command(ctx: ToolContext, args: dict[str, Any]) -> str:
    return shell_tools.run_command(
        ctx.working_dir,
        command=args["command"],
        timeout=int(args.get("timeout", 60)),
    )


def _tool_run_python_file(ctx: ToolContext, args: dict[str, Any]) -> str:
    return shell_tools.run_python_file(
        ctx.working_dir,
        file_path=args["file_path"],
        args=list(args.get("args") or []),
        timeout=int(args.get("timeout", 60)),
    )


_TOOL_TABLE: dict[str, Callable[[ToolContext, dict[str, Any]], str]] = {
    "get_files_info": _tool_get_files_info,
    "get_file_content": _tool_get_file_content,
    "grep_search": _tool_grep_search,
    "write_file": _tool_write_file,
    "run_command": _tool_run_command,
    "run_python_file": _tool_run_python_file,
}


def dispatch(name: str, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    """Run the named tool. Errors are captured and returned as ``is_error``."""
    if name not in _TOOL_TABLE:
        return ToolResult(
            name=name,
            output=f"Unknown tool: {name!r}",
            is_error=True,
        )
    impl = _TOOL_TABLE[name]
    try:
        output = impl(ctx, args or {})
    except KeyError as exc:
        return ToolResult(
            name=name,
            output=f"Missing required argument: {exc.args[0]!r}",
            is_error=True,
        )
    except Exception as exc:
        return ToolResult(name=name, output=f"{type(exc).__name__}: {exc}", is_error=True)
    return ToolResult(name=name, output=output, is_error=False)
