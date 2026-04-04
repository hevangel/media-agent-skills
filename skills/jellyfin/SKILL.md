---
name: jellyfin
description: "Interact with the Jellyfin media server API to list libraries, search media, get item details, export metadata, and trigger library rescans. Use when working with Jellyfin servers."
license: MIT
compatibility: Requires Python 3.13+, uv, and jellyfin-apiclient-python
---

# Jellyfin API

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
JELLYFIN_HOST=http://localhost:8096
JELLYFIN_API_KEY=your_api_key
```

## Reference

- Jellyfin API documentation: https://api.jellyfin.org/
- Python API Client: https://github.com/jellyfin/jellyfin-apiclient-python
- Code Snippets: `scripts/`

**Note:** Scripts use `config.py` for credentials and `client.py` for client setup.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `config.py` | Configuration loader (from `.env`) |
| `client.py` | API client setup with authentication |
| `list_libraries.py` | List all libraries |
| `get_library_items.py` | Get items with media type filtering |
| `search_media.py` | Search by term, type, and year |
| `get_item_details.py` | Full metadata for an item |
| `get_recently_added.py` | Recently added items |
| `refresh_library.py` | Trigger library rescan |
| `dump_library_to_json.py` | Export library to JSON |
| `get_system_info.py` | Server system information |

## Key Patterns

### API Key Authentication

```python
from jellyfin_apiclient_python import JellyfinClient

client = JellyfinClient()
client.config.data["app.name"] = "ai_agents"
client.config.data["auth.ssl"] = False
client.authenticate(
    {"Servers": [{"AccessToken": API_KEY, "address": SERVER_URL}]},
    discover=False,
)
```

### API Access

```python
libraries = client.jellyfin.virtual_folders()
item = client.jellyfin.get_item(item_id)
result = client.jellyfin.search_media_items(term="Movie Name", media="Movie")
```

### Item Types for Filtering

`Movie`, `Series`, `Season`, `Episode`, `Audio`, `MusicAlbum`, `MusicArtist`, `Book`, `AudioBook`, `BoxSet`, `Playlist`

## Usage Examples

```bash
cd skills/jellyfin/scripts
uv run python list_libraries.py
uv run python search_media.py "Gundam" Movie
uv run python get_item_details.py <item_id>
uv run python dump_library_to_json.py <library_id>
```

## Notes

- Use `client.py` and `get_jellyfin_client()` as the starting point for all API scripts.
- Temporary files go in `$WORKSPACE_PATH/temp/`.
