# AI Agents

A collection of [Agent Skills](https://agentskills.io/) for managing media libraries, downloading content, and automating workflows. Skills follow the open [Agent Skills specification](https://agentskills.io/specification) and work with any compatible AI coding agent.

## Skills

| Skill | Description |
|-------|-------------|
| [audiobooks](skills/audiobooks/) | Manage audiobook libraries, download covers, embed metadata, search AudiobookBay |
| [audiobookshelf](skills/audiobookshelf/) | Audiobookshelf server API — libraries, metadata, authors, rescans |
| [copilot-sdk](skills/copilot-sdk/) | GitHub Copilot SDK — programmatically call Copilot from Python |
| [ebook](skills/ebook/) | EPUB metadata extraction, updates, cover embedding, series info |
| [imdb](skills/imdb/) | IMDB lookup — search movies/TV/people, popular & upcoming titles |
| [jellyfin](skills/jellyfin/) | Jellyfin server API — libraries, search, metadata, rescans |
| [kavita](skills/kavita/) | Kavita reading server API — libraries, series, metadata, rescans |
| [libgen](skills/libgen/) | Search and download ebooks from Library Genesis |
| [nyaa](skills/nyaa/) | Search and download anime torrents from nyaa.si |
| [plex](skills/plex/) | Plex Media Server API — libraries, search, playlists, collections |
| [qbittorrent](skills/qbittorrent/) | qBittorrent client — add, pause, resume, delete torrents |
| [tvdb](skills/tvdb/) | TheTVDB lookup — search series/movies/people, episodes, seasons, artwork |
| [yts](skills/yts/) | Search and download movie torrents from YTS ([ytz.mx](https://ytz.mx/)) |

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
git clone https://github.com/hevangel/ai_agents.git
cd ai_agents
uv sync
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your actual credentials and paths
```

See [.env.example](.env.example) for all available settings.

## Usage

### With Claude Code

Register this repo as a plugin marketplace:

```
/plugin marketplace add hevangel/ai_agents
```

Then install skill groups:

```
/plugin install media-server-skills@ai-agents-skills
/plugin install torrent-skills@ai-agents-skills
/plugin install ebook-skills@ai-agents-skills
/plugin install audiobook-skills@ai-agents-skills
/plugin install ai-tools@ai-agents-skills
```

### With VS Code Copilot

Skills in `skills/` are automatically discovered when the repo is open as a workspace. Reference a skill by mentioning it in chat, or use `#<skill-name>`.

### With Other Agent Tools

Any tool supporting the [Agent Skills specification](https://agentskills.io/clients) can use these skills. Point the tool at the `skills/` directory.

### Running Scripts Directly

```bash
# Run any skill script
uv run python skills/<skill>/scripts/<script>.py

# Example: search Jellyfin
uv run python skills/jellyfin/scripts/search_media.py "Gundam" Movie

# Example: list Plex libraries
uv run python skills/plex/scripts/list_libraries.py
```

## Project Structure

```
skills/                  # Agent skills (agentskills.io format)
  <skill-name>/
    SKILL.md             # Metadata + instructions
    scripts/             # Code snippets and modules
.claude-plugin/          # Claude Code marketplace config
mcp_servers/             # MCP server implementations
anime_organizer/         # Anime library organizer
anime_database/          # Anime metadata (MongoDB)
temp/                    # Temporary files (gitignored)
```

## Updating AI CLI Tools

```bash
# Windows
.\update_agents.ps1

# Linux / macOS
./update_agents.sh
```

## Cross-Platform Support

- All Python code uses `pathlib.Path` for cross-platform path handling
- Shell scripts provided for both Windows (PowerShell) and Linux/macOS (Bash)
- Library paths configured via environment variables (no hardcoded OS-specific paths)

## License

[MIT](LICENSE)
