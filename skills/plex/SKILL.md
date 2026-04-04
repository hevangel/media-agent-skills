---
name: plex
description: "Interact with a Plex Media Server to list libraries, search media, get item details, manage playlists and collections, export metadata, and trigger library rescans. Use when working with Plex servers."
license: MIT
compatibility: Requires Python 3.13+, uv, and python-plexapi
---

# Plex Media Server API

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your_token
PLEX_USERNAME=your_username
PLEX_PASSWORD=your_password
```

Authentication methods (tried in order):
1. **Direct token** (recommended): `PLEX_URL` + `PLEX_TOKEN`
2. **MyPlex account** (fallback): `PLEX_USERNAME` + `PLEX_PASSWORD`

### Quick Token Setup

```bash
cd skills/plex/scripts
uv run python get_token.py
```

Supports MyPlex login, browser-based PIN auth, or manual token entry.

## Reference

- python-plexapi docs: https://python-plexapi.readthedocs.io/
- Code Snippets: `scripts/`

## Available Scripts

| Script | Purpose |
|--------|---------|
| `config.py` | Loads credentials from `.env` |
| `client.py` | Creates authenticated `PlexServer` instance |
| `get_token.py` | Interactive token helper |
| `list_libraries.py` | List all libraries |
| `get_library_items.py` | Get items from a library |
| `search_media.py` | Search by query, type, library |
| `get_item_details.py` | Full metadata for an item |
| `get_recently_added.py` | Recently added items |
| `refresh_library.py` | Trigger library refresh/scan |
| `dump_library_to_json.py` | Export library to JSON |
| `get_server_info.py` | Server info, active sessions |

## Key Patterns

### API Access

```python
from plexapi.server import PlexServer

plex = PlexServer(baseurl, token)
libraries = plex.library.sections()
section = plex.library.section('Movies')
results = plex.search('query')
item = plex.fetchItem(rating_key)
```

### Common Operations

- **Libraries**: `plex.library.sections()`, `plex.library.section('name')`
- **Search**: `plex.search('query')`, `section.search(query=..., libtype=...)`
- **Items**: `section.all()`, `plex.fetchItem(key)`, `section.recentlyAdded()`
- **Refresh**: `section.refresh()`, `section.update()`
- **TV Shows**: `show.seasons()`, `show.episodes()`, `show.episode(season=N, episode=M)`
- **Playlists**: `plex.playlists()`, `plex.createPlaylist(title, items=items)`
- **Collections**: `section.collections()`, `collection.items()`

### Item Metadata

- `title`, `year`, `summary`, `rating`, `contentRating`
- `[g.tag for g in item.genres]`, `[d.tag for d in item.directors]`
- `[g.id for g in item.guids]` (IMDB, TMDB, TVDB)
- `item.media[0].parts[0].file` (file path)

### Library/Item Types

`movie`, `show`, `season`, `episode`, `artist`, `album`, `track`, `photo`

## Usage Examples

```bash
cd skills/plex/scripts
uv run python list_libraries.py
uv run python search_media.py "Midway"
uv run python get_recently_added.py "Movies" 10
uv run python dump_library_to_json.py "Movies"
uv run python refresh_library.py "Movies"
```

## Notes

- Use `client.py` and `get_plex_client()` as the starting point.
- Temporary files go in `$WORKSPACE_PATH/temp/`.
