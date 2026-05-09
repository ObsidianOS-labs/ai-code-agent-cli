# ai-code-agent-cli

An autonomous code agent CLI with multi-provider LLM support and an
interactive terminal UI.

The agent reads, searches, edits, and runs code in a sandboxed working
directory through six tools — `get_files_info`, `get_file_content`,
`grep_search`, `write_file`, `run_command`, `run_python_file` — and
follows the plan → explore → implement → verify → respond workflow
defined in [`src/ai_code_agent/prompts/system.md`](src/ai_code_agent/prompts/system.md).

## Features

- **Pluggable providers** — OpenAI, Anthropic, Google Gemini, and Ollama
  (local). Switch at any time with `/provider <name>`.
- **Interactive terminal UI** built on [Rich](https://github.com/Textualize/rich)
  + [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit):
  syntax-highlighted tool calls, panelized assistant turns, persistent
  input history.
- **Slash commands** — `/help`, `/status`, `/provider`, `/model`,
  `/cwd`, `/clear`, `/exit`.
- **Sandboxed file I/O** — every path is resolved relative to the
  working directory; traversal (`../`) and absolute paths to
  `/etc`, `~/.ssh`, etc. are rejected.
- **One-shot mode** — `ai-code-agent ask "..."` for non-interactive use.
- **Config layering** — CLI flags > env vars (`.env` supported) >
  `~/.config/ai-code-agent/config.toml` > defaults.

## Install

Requires Python ≥ 3.10.

```bash
# Clone and install in editable mode with the providers you want
git clone https://github.com/ObsidianOS-labs/ai-code-agent-cli.git
cd ai-code-agent-cli

pip install -e ".[all]"          # all providers + core
# or pick a subset:
pip install -e ".[openai]"
pip install -e ".[anthropic]"
pip install -e ".[gemini]"
pip install -e .                  # core only (Ollama works without extras)
```

## Configure

Copy `.env.example` to `.env` and fill in the keys you have:

```bash
cp .env.example .env
$EDITOR .env
```

Or export the variables directly:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
export OLLAMA_BASE_URL=http://localhost:11434   # default
```

You can also persist defaults in `~/.config/ai-code-agent/config.toml`:

```toml
provider = "anthropic"
model = "claude-3-5-sonnet-latest"
max_tool_iterations = 25
```

## Run

Interactive mode (default):

```bash
ai-code-agent                                  # uses default provider
ai-code-agent --provider gemini --model gemini-1.5-pro
ai-code-agent --cwd ~/projects/my-app          # operate in a different dir
```

Inside the REPL:

```
you> /help
you> /provider anthropic
you> /model claude-3-5-haiku-latest
you> Read the package.json and tell me what frameworks are used.
```

One-shot:

```bash
ai-code-agent ask "Run the tests and summarize failures."
```

List supported providers and their default models:

```bash
ai-code-agent providers
```

## Project layout

```
src/ai_code_agent/
├── agent.py              # plan→tools→respond loop
├── cli.py                # typer entry point + REPL
├── config.py             # env / .env / TOML loader
├── prompts/system.md     # CodeAgent system prompt
├── providers/            # OpenAI / Anthropic / Gemini / Ollama adapters
│   ├── base.py
│   └── factory.py
├── safety.py             # path-sandbox helpers
├── tools/                # the six tools the agent can call
│   ├── dispatcher.py
│   ├── files.py
│   ├── schema.py
│   ├── search.py
│   └── shell.py
└── ui.py                 # Rich + prompt_toolkit terminal UI
tests/                    # pytest suite (no LLM required)
```

## Development

```bash
pip install -e ".[dev,all]"
pytest -q
ruff check .
ruff format --check .
```

## License

[MIT](LICENSE)
