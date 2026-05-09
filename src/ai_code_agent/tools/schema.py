"""Normalized JSON-Schema definitions for every tool exposed to the LLM.

Provider adapters convert these into provider-specific tool/function-calling
formats (OpenAI ``functions``, Anthropic ``tools``, Gemini ``function_declarations``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any]


TOOL_SCHEMAS: list[ToolSchema] = [
    ToolSchema(
        name="get_files_info",
        description=(
            "List files and directories with their sizes inside the given directory. "
            "All paths are relative to the working directory."
        ),
        parameters={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Relative directory path. Use '.' for the working directory root.",
                    "default": ".",
                },
            },
            "required": [],
        },
    ),
    ToolSchema(
        name="get_file_content",
        description=(
            "Read the content of a file. Output may be truncated for very large files; "
            "use grep_search to locate specific lines."
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file.",
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum bytes to return (default 64 KiB).",
                    "default": 65536,
                },
            },
            "required": ["file_path"],
        },
    ),
    ToolSchema(
        name="grep_search",
        description=(
            "Search files in a directory for a regular expression pattern. "
            "Returns file:line:matched_text rows."
        ),
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Python regular expression to match.",
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search recursively. Use '.' for the working directory root.",
                    "default": ".",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matching lines to return (default 200).",
                    "default": 200,
                },
            },
            "required": ["pattern"],
        },
    ),
    ToolSchema(
        name="write_file",
        description=(
            "Create or fully overwrite a file with the supplied content. "
            "Pass the FULL intended file content — never a diff or snippet."
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file. Parent directories are created as needed.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete new content of the file.",
                },
            },
            "required": ["file_path", "content"],
        },
    ),
    ToolSchema(
        name="run_command",
        description=(
            "Execute a shell command in the working directory. "
            "Returns combined stdout/stderr and the exit code. "
            "Subject to a configurable timeout."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 60).",
                    "default": 60,
                },
            },
            "required": ["command"],
        },
    ),
    ToolSchema(
        name="run_python_file",
        description=(
            "Execute a specific Python file inside the working directory using the current "
            "Python interpreter, with optional CLI arguments."
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to a .py file.",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of arguments to pass to the script.",
                    "default": [],
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 60).",
                    "default": 60,
                },
            },
            "required": ["file_path"],
        },
    ),
]


def get_schema(name: str) -> ToolSchema:
    for schema in TOOL_SCHEMAS:
        if schema.name == name:
            return schema
    raise KeyError(f"Unknown tool: {name}")
