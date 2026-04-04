---
name: copilot-sdk
description: "Use GitHub Copilot SDK to programmatically call Copilot from Python. Use when integrating AI capabilities via Copilot CLI into applications."
license: MIT
compatibility: Requires GitHub Copilot subscription and gh CLI authenticated
---

# GitHub Copilot SDK for Python

The GitHub Copilot SDK is a multi-platform SDK for integrating GitHub Copilot Agent into apps and services. It exposes the same engine behind Copilot CLI, providing a production-tested agent runtime you can invoke programmatically.

> **Note:** This SDK is in technical preview and may change in breaking ways.

## Reference

- Code Snippets: `scripts/`
- GitHub Repository: https://github.com/github/copilot-sdk
- PyPI Package: https://pypi.org/project/github-copilot-sdk/

## Prerequisites

1. **GitHub Copilot Subscription**: Required
2. **Copilot CLI**: Must be installed (`gh extension install github/gh-copilot`)
3. **Authentication**: Must be logged into GitHub CLI (`gh auth login`)

## Installation

```bash
uv pip install github-copilot-sdk
```

## Architecture

```
Your Application
       |
  SDK Client (Python)
       | JSON-RPC
  Copilot CLI (server mode)
```

## API Reference

### CopilotClient Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cli_path` | str | "copilot" | Path to CLI executable |
| `cli_url` | str | None | URL of existing CLI server |
| `cwd` | str | None | Working directory for CLI process |
| `port` | int | 0 | Server port (0 = random) |
| `use_stdio` | bool | True | Use stdio transport |
| `auto_start` | bool | True | Auto-start server |
| `auto_restart` | bool | True | Auto-restart on crash |

### CopilotClient Methods

| Method | Description |
|--------|-------------|
| `await client.start()` | Start the CLI server |
| `await client.stop()` | Stop the CLI server |
| `await client.create_session(config)` | Create a conversation session |
| `await client.resume_session(session_id)` | Resume existing session |
| `await client.get_models()` | Get available models |

### SessionConfig

| Option | Type | Description |
|--------|------|-------------|
| `model` | str | Model to use ("gpt-5", "claude-sonnet-4.5", etc.) |
| `tools` | list[Tool] | Custom tools exposed to the CLI |
| `streaming` | bool | Enable streaming responses |
| `mcp_servers` | dict | MCP server configurations |

### Event Types

| Event Type | Description |
|------------|-------------|
| `assistant.message` | Final assistant message |
| `assistant.message_delta` | Streaming message chunk |
| `session.idle` | Session finished processing |
| `tool.call` | Tool invocation |
| `error` | Error event |

## Available Models

- `gpt-4.1`, `gpt-5`, `claude-sonnet-4.5`, `o3-mini`, `gemini-2.5-pro`

## Basic Usage

```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()
    session = await client.create_session({"model": "gpt-4.1"})
    response = await session.send_and_wait({"prompt": "What is Python?"})
    print(response.data.content)
    await session.destroy()
    await client.stop()

asyncio.run(main())
```
