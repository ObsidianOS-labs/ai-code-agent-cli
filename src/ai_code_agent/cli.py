"""Typer-based CLI entry point and the interactive REPL."""

from __future__ import annotations

import shlex
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ai_code_agent import __version__
from ai_code_agent.agent import Agent, AgentObserver
from ai_code_agent.config import SUPPORTED_PROVIDERS, load_config
from ai_code_agent.prompts import load_system_prompt
from ai_code_agent.providers import build_provider
from ai_code_agent.providers.base import ProviderError, ToolCall
from ai_code_agent.providers.catalog import entries_by_category
from ai_code_agent.tools import ToolResult
from ai_code_agent.ui import TerminalUI, default_history_path

app = typer.Typer(
    name="ai-code-agent",
    help="An autonomous code agent CLI with multi-provider LLM support.",
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"ai-code-agent-cli {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    provider: str | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider id. Run `ai-code-agent providers` to see all options.",
    ),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Model name for the chosen provider."
    ),
    working_dir: Path | None = typer.Option(
        None,
        "--cwd",
        "-C",
        help="Working directory the agent operates in (default: current dir).",
    ),
    config_path: Path | None = typer.Option(
        None,
        "--config",
        help="Path to a TOML config file (default: ~/.config/ai-code-agent/config.toml).",
    ),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        help="Override base URL (used by --provider custom for OpenAI-compatible endpoints).",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        help="Override API key for --provider custom.",
    ),
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Launch the interactive code agent if no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    _run_repl(
        provider=provider,
        model=model,
        working_dir=working_dir,
        config_path=config_path,
        base_url=base_url,
        api_key=api_key,
    )


@app.command("providers")
def list_providers(
    category: str | None = typer.Option(
        None, "--category", "-c", help="Filter to a single category (case-insensitive substring)."
    ),
) -> None:
    """List supported providers grouped by category, with default models and env vars."""
    console = Console()
    for cat, items in entries_by_category().items():
        if category and category.lower() not in cat.lower():
            continue
        table = Table(
            title=f"[bold]{cat}[/bold]",
            title_justify="left",
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 2),
        )
        table.add_column("id", style="cyan", no_wrap=True)
        table.add_column("provider")
        table.add_column("default model")
        table.add_column("env var")
        for entry in items:
            env = entry.env_var or ("—" if entry.kind != "openai_compat" else "")
            model_text = entry.default_model or "(none)"
            table.add_row(entry.id, entry.display_name, model_text, env or "—")
        console.print(table)
        console.print()


@app.command("ask")
def ask(
    prompt: str = typer.Argument(..., help="One-shot prompt to send to the agent."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
    working_dir: Path | None = typer.Option(None, "--cwd", "-C"),
    base_url: str | None = typer.Option(None, "--base-url"),
    api_key: str | None = typer.Option(None, "--api-key"),
) -> None:
    """Send a single prompt and print the result (non-interactive)."""
    console = Console()
    try:
        cfg = load_config(
            cli_provider=provider,
            cli_model=model,
            cli_working_dir=working_dir,
            cli_base_url=base_url,
            cli_api_key=api_key,
        )
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        console.print(f"[red]config error:[/red] {exc}")
        raise typer.Exit(2) from exc

    if not cfg.keys.has_key_for(cfg.provider):
        console.print(
            f"[red]Missing credentials for provider {cfg.provider!r}.[/red] See .env.example."
        )
        raise typer.Exit(2)

    try:
        provider_obj = build_provider(cfg, system_prompt=load_system_prompt())
    except ProviderError as exc:
        console.print(f"[red]provider error:[/red] {exc}")
        raise typer.Exit(2) from exc

    ui = TerminalUI(console=console, history_file=default_history_path())
    observer = _UIObserver(ui)
    agent = Agent(
        provider=provider_obj,
        working_dir=cfg.working_dir,
        max_iterations=cfg.max_tool_iterations,
        observer=observer,
    )
    final = agent.run_turn(prompt)
    if not final and not observer.printed_any_text:
        ui.info("(no text response)")


# ── REPL ─────────────────────────────────────────────────────────────


class _UIObserver(AgentObserver):
    def __init__(self, ui: TerminalUI):
        self.ui = ui
        self.printed_any_text = False

    def on_assistant_text(self, text: str) -> None:
        if text.strip():
            self.printed_any_text = True
            self.ui.assistant_text(text)

    def on_tool_call(self, call: ToolCall) -> None:
        self.ui.tool_call(call)

    def on_tool_result(self, call: ToolCall, result: ToolResult) -> None:
        self.ui.tool_result(call, result)

    def on_iteration_limit(self, limit: int) -> None:
        self.ui.warning(f"Hit tool-iteration limit ({limit}). Stopping.")


def _run_repl(
    *,
    provider: str | None,
    model: str | None,
    working_dir: Path | None,
    config_path: Path | None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> None:
    console = Console()
    try:
        cfg = load_config(
            cli_provider=provider,
            cli_model=model,
            cli_working_dir=working_dir,
            config_path=config_path,
            cli_base_url=base_url,
            cli_api_key=api_key,
        )
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        console.print(f"[red]config error:[/red] {exc}")
        raise typer.Exit(2) from exc

    if not cfg.keys.has_key_for(cfg.provider):
        console.print(
            f"[red]Missing API key for provider {cfg.provider!r}.[/red] "
            f"Set the appropriate env var (see .env.example)."
        )
        raise typer.Exit(2)

    system_prompt = load_system_prompt()
    try:
        provider_obj = build_provider(cfg, system_prompt=system_prompt)
    except ProviderError as exc:
        console.print(f"[red]provider error:[/red] {exc}")
        raise typer.Exit(2) from exc

    ui = TerminalUI(console=console, history_file=default_history_path())
    observer = _UIObserver(ui)
    agent = Agent(
        provider=provider_obj,
        working_dir=cfg.working_dir,
        max_iterations=cfg.max_tool_iterations,
        observer=observer,
    )

    ui.banner(provider_name=provider_obj.display_name(), working_dir=cfg.working_dir)

    while True:
        try:
            user_input = ui.ask()
        except (EOFError, KeyboardInterrupt):
            console.print()
            ui.info("bye!")
            return

        text = user_input.strip()
        if not text:
            continue

        if text.startswith("/"):
            stop = _handle_slash(text, ui=ui, agent=agent, cfg=cfg, system_prompt=system_prompt)
            if stop:
                return
            continue

        try:
            agent.run_turn(text)
        except ProviderError as exc:
            ui.error(str(exc))
        except Exception as exc:
            ui.error(f"{type(exc).__name__}: {exc}")


def _handle_slash(
    line: str,
    *,
    ui: TerminalUI,
    agent: Agent,
    cfg,
    system_prompt: str,
) -> bool:
    """Return ``True`` if the REPL should stop."""
    try:
        parts = shlex.split(line)
    except ValueError as exc:
        ui.error(f"could not parse command: {exc}")
        return False
    if not parts:
        return False
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ("/exit", "/quit"):
        ui.info("bye!")
        return True

    if cmd == "/help":
        ui.show_help()
        return False

    if cmd == "/status":
        ui.show_status(
            provider_name=agent.provider.name,
            model=agent.provider.model,
            working_dir=agent.working_dir,
            message_count=len(agent.messages),
        )
        return False

    if cmd == "/clear":
        agent.reset()
        ui.info("conversation history cleared")
        return False

    if cmd == "/cwd":
        if not args:
            ui.info(f"cwd = {agent.working_dir}")
            return False
        new_dir = Path(args[0]).expanduser().resolve()
        if not new_dir.is_dir():
            ui.error(f"not a directory: {new_dir}")
            return False
        agent.working_dir = new_dir
        cfg.working_dir = new_dir
        ui.info(f"cwd → {new_dir}")
        return False

    if cmd == "/provider":
        if not args:
            ui.info(
                f"provider = {agent.provider.name}  "
                f"({len(SUPPORTED_PROVIDERS)} supported — run "
                f"'ai-code-agent providers' for the full list)"
            )
            return False
        new_provider = args[0].lower()
        if new_provider not in SUPPORTED_PROVIDERS:
            ui.error(f"unsupported provider {new_provider!r}")
            return False
        old_provider = cfg.provider
        old_model = cfg.model
        cfg.provider = new_provider
        cfg.model = None
        if not cfg.keys.has_key_for(new_provider):
            ui.error(f"missing API key for {new_provider!r}; not switching")
            cfg.provider = old_provider
            cfg.model = old_model
            return False
        try:
            agent.provider = build_provider(cfg, system_prompt=system_prompt)
        except ProviderError as exc:
            ui.error(str(exc))
            cfg.provider = old_provider
            cfg.model = old_model
            return False
        agent.reset()
        ui.info(f"provider → {agent.provider.display_name()} (history cleared)")
        return False

    if cmd == "/model":
        if not args:
            ui.info(f"model = {agent.provider.model}")
            return False
        new_model = args[0]
        old_model = cfg.model
        cfg.model = new_model
        try:
            agent.provider = build_provider(cfg, system_prompt=system_prompt)
        except ProviderError as exc:
            ui.error(str(exc))
            cfg.model = old_model
            return False
        ui.info(f"model → {agent.provider.display_name()}")
        return False

    ui.error(f"unknown command: {cmd}. type /help for help.")
    return False


if __name__ == "__main__":
    app()
