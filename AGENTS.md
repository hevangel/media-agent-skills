# AI Agents — Coding Guidelines

## Basic Standards

- This repo uses **uv** for Python package management; always run scripts with `uv run python`
- Use **4 spaces** for indentation (no tabs)
- Use **snake_case** for function and variable names
- Do not call `python -c` with generated code; create a Python script then run it
- Always print progress messages when creating Python scripts

## Project Structure

```
skills/                  # Agent skills (agentskills.io format)
  <skill-name>/
    SKILL.md             # Required: metadata + instructions
    scripts/             # Code snippets and reusable modules
mcp_servers/             # MCP server implementations
anime_organizer/         # Anime library organizer
anime_database/          # Anime metadata (MongoDB)
audiobooks_organizer/    # Legacy audiobook prompts
ebook_organizer/         # Legacy ebook prompts
prompts/                 # Standalone prompt files
temp/                    # Temporary scripts and data (gitignored)
```

### Skills Directory

Skills follow the [Agent Skills](https://agentskills.io/specification) open format:

- Each skill lives in `skills/<skill-name>/` with a `SKILL.md` file
- Directory names: **lowercase letters, numbers, and hyphens only**
- The `name` field in YAML frontmatter must match the directory name
- Code snippets go in `scripts/`; assets go in `assets/`

The `skills/` directory is the **single source of truth**. Symlinks/junctions for
different AI tools (`.github/skills/`, `.claude/skills`, `.cursor/skills`, `.agent/skills`)
all point back to `skills/`.

### Temporary Files

- Create temporary scripts and test files under `temp/`
- Store intermediate data (JSON, etc.) under `temp/`
- `temp/` is gitignored — do not commit temporary files

## File Handling

- Path handling must support **both Windows and Linux** (use `pathlib.Path`)
- Reference library paths via environment variables, not hardcoded paths

## Configuration

- Store all sensitive data (usernames, passwords, API keys, hosts) in `.env`
- Never commit `.env` to version control
- See `.env.example` for all available configuration variables
- Skills reference env vars in their `.env` code blocks with placeholder values

## Cross-Platform Support

This repo supports both Windows and Linux:

- Use `pathlib.Path` for all file paths
- Shell scripts: `update_agents.ps1` (Windows) and `update_agents.sh` (Linux/macOS)
- Avoid OS-specific path separators in Python code

## Claude Code Plugin Marketplace

This repo is a Claude Code plugin marketplace. To use:

```
/plugin marketplace add <owner>/<repo>
```

See `.claude-plugin/marketplace.json` for available plugin groups.
