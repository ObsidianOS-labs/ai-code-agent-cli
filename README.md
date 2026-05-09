# ai-code-agent-cli

An autonomous code agent CLI with multi-provider LLM support and an
interactive terminal UI.

The agent reads, searches, edits, and runs code in a sandboxed working
directory through six tools — `get_files_info`, `get_file_content`,
`grep_search`, `write_file`, `run_command`, `run_python_file` — and
follows the plan → explore → implement → verify → respond workflow
defined in [`src/ai_code_agent/prompts/system.md`](src/ai_code_agent/prompts/system.md).

## Features

- **40+ pluggable providers** out of the box — see [`Provider catalog`](#provider-catalog)
  below or run `ai-code-agent providers`. Native adapters for OpenAI,
  Anthropic, Gemini, Ollama, Azure OpenAI, Vertex (Anthropic), AWS
  Bedrock; one shared OpenAI-compatible adapter for Groq, Together,
  DeepSeek, Mistral, OpenRouter, Fireworks, Perplexity, xAI, Cerebras,
  Moonshot/Kimi, Deep Infra, Nvidia NIM, Hugging Face, Nebius, Novita,
  SiliconFlow, Zhipu/Z.AI, Alibaba DashScope, ModelScope, StepFun,
  MiniMax, OVHcloud, Scaleway, Upstage, Poe, Venice, Vercel AI Gateway,
  GitHub Models, Cohere, LM Studio, Friendli, 302.AI, AIHubMix, … plus
  a `--provider custom --base-url ...` escape hatch.
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
you> /provider groq
you> /model llama-3.3-70b-versatile
you> Read the package.json and tell me what frameworks are used.
```

One-shot:

```bash
ai-code-agent ask "Run the tests and summarize failures."
```

List all 40+ supported providers (grouped by category, with default
models and env var names):

```bash
ai-code-agent providers
ai-code-agent providers --category gateway
```

## Provider catalog

Most providers expose the OpenAI Chat Completions API at a custom
`base_url`, so a single OpenAI-compatible adapter handles all of them
— configured by the catalog at
[`src/ai_code_agent/providers/catalog.py`](src/ai_code_agent/providers/catalog.py).
Providers with genuinely different APIs (Anthropic, Gemini, Ollama,
Azure, Vertex, Bedrock) get their own thin adapters.

Usage examples:

```bash
ai-code-agent --provider groq                                # GROQ_API_KEY
ai-code-agent --provider together --model meta-llama/Llama-3.3-70B-Instruct-Turbo
ai-code-agent --provider deepseek                            # DEEPSEEK_API_KEY
ai-code-agent --provider openrouter --model anthropic/claude-3.5-sonnet
ai-code-agent --provider azure --model my-deployment-name
ai-code-agent --provider vertex_anthropic                    # gcloud ADC
ai-code-agent --provider bedrock                             # AWS creds
ai-code-agent --provider lmstudio                            # local LM Studio
ai-code-agent --provider custom --base-url https://my.host/v1 --api-key sk-... --model my-model
```

Don't see a provider you need? Either:

1. Use `--provider custom --base-url <openai-compatible-url> --api-key
   <key>` (works for any provider with an OpenAI-compatible Chat
   Completions endpoint), or
2. Open an issue / PR adding it to `catalog.py` — each entry is a
   single `ProviderEntry(...)` literal.

## Project layout

```
src/ai_code_agent/
├── agent.py              # plan→tools→respond loop
├── cli.py                # typer entry point + REPL
├── config.py             # env / .env / TOML loader
├── prompts/system.md     # CodeAgent system prompt
├── providers/            # adapter per shape + the provider catalog
│   ├── base.py           # Provider ABC + Message/ToolCall types
│   ├── catalog.py        # 40+ provider presets
│   ├── openai_compat.py  # generic OpenAI-compatible adapter
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── ollama_provider.py
│   ├── openai_provider.py
│   ├── azure_provider.py
│   ├── vertex_anthropic_provider.py
│   ├── bedrock_provider.py
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
