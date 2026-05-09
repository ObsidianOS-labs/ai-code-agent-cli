"""Interactive terminal UI built on Rich + prompt_toolkit."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ai_code_agent import __version__
from ai_code_agent.providers.base import ToolCall
from ai_code_agent.tools import ToolResult

BANNER = r"""
   _    ___    ____          _              _                  _
  / \  |_ _|  / ___|___   __| | ___    /\ \/ /  __ _  ___ _ __| |_
 / _ \  | |  | |   / _ \ / _` |/ _ \  /  \  /  / _` |/ _ \ '__| __|
/ ___ \ | |  | |__| (_) | (_| |  __/ / /\/ /  | (_| |  __/ |  | |_
\_/   \_\___| \____\___/ \__,_|\___| \/  \/    \__, |\___|_|   \__|
                                                |___/
"""


@dataclass
class TerminalUI:
    console: Console
    history_file: Path
    on_exit: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._kb = KeyBindings()
        self._session: PromptSession[str] = PromptSession(
            history=FileHistory(str(self.history_file)),
            key_bindings=self._kb,
            multiline=False,
        )

    # ── Output ────────────────────────────────────────────────────────
    def banner(self, *, provider_name: str, working_dir: Path) -> None:
        self.console.print(Text(BANNER.rstrip(), style="bold cyan"))
        self.console.print(
            Panel.fit(
                f"[bold]ai-code-agent-cli[/bold]  v{__version__}\n"
                f"provider:  [yellow]{provider_name}[/yellow]\n"
                f"cwd:       [magenta]{working_dir}[/magenta]\n\n"
                "Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit.",
                title="Ready",
                border_style="cyan",
            )
        )

    def info(self, message: str) -> None:
        self.console.print(f"[dim]· {message}[/dim]")

    def error(self, message: str) -> None:
        self.console.print(f"[bold red]error[/bold red] {message}")

    def warning(self, message: str) -> None:
        self.console.print(f"[bold yellow]warning[/bold yellow] {message}")

    def assistant_text(self, text: str) -> None:
        if not text:
            return
        self.console.print(
            Panel(
                Markdown(text),
                title="assistant",
                title_align="left",
                border_style="green",
            )
        )

    def tool_call(self, call: ToolCall) -> None:
        try:
            args_pretty = json.dumps(call.arguments, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            args_pretty = repr(call.arguments)
        body = Syntax(args_pretty, "json", theme="ansi_dark", word_wrap=True)
        self.console.print(
            Panel(
                body,
                title=f"tool · [bold]{call.name}[/bold]",
                title_align="left",
                border_style="blue",
            )
        )

    def tool_result(self, call: ToolCall, result: ToolResult) -> None:
        text = result.output
        max_lines = 30
        lines = text.splitlines()
        if len(lines) > max_lines:
            head = "\n".join(lines[:max_lines])
            text = head + f"\n... [output truncated to {max_lines} lines]"
        border = "red" if result.is_error else "magenta"
        title = f"result · {call.name}"
        if result.is_error:
            title += " [red](error)[/red]"
        self.console.print(
            Panel(
                Text(text, no_wrap=False),
                title=title,
                title_align="left",
                border_style=border,
            )
        )

    def show_status(
        self, *, provider_name: str, model: str, working_dir: Path, message_count: int
    ) -> None:
        table = Table(show_header=False, box=None)
        table.add_row("[bold]provider[/bold]", provider_name)
        table.add_row("[bold]model[/bold]", model)
        table.add_row("[bold]cwd[/bold]", str(working_dir))
        table.add_row("[bold]history[/bold]", f"{message_count} messages")
        self.console.print(Panel.fit(table, title="status", border_style="cyan"))

    def show_help(self) -> None:
        table = Table(title="Commands", title_style="bold cyan", header_style="bold")
        table.add_column("command", style="yellow", no_wrap=True)
        table.add_column("description")
        table.add_row("/help", "Show this list of slash commands")
        table.add_row("/status", "Show provider, model, working directory, and history size")
        table.add_row("/provider <name>", "Switch provider (openai | anthropic | gemini | ollama)")
        table.add_row("/model <name>", "Switch model for the current provider")
        table.add_row("/cwd [path]", "Print or change the agent's working directory")
        table.add_row("/clear", "Clear the conversation history")
        table.add_row("/exit, /quit", "Exit the CLI (Ctrl-D also works)")
        self.console.print(table)

    # ── Input ─────────────────────────────────────────────────────────
    def ask(self, prompt: str = "you") -> str:
        try:
            text = self._session.prompt(FormattedText([("class:prompt", f"{prompt}> ")]))
        except (EOFError, KeyboardInterrupt):
            raise
        return text


def default_history_path() -> Path:
    return Path.home() / ".cache" / "ai-code-agent" / "history"
