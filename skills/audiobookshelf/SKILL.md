---
name: audiobookshelf
description: "Interact with the Audiobookshelf API to manage audiobook libraries, update metadata, scan directories, and manage authors. Use when working with Audiobookshelf server instances."
license: MIT
compatibility: Requires Python 3.13+, uv, and aioaudiobookshelf
---

# Audiobookshelf API

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
AUDIOBOOKSHELF_HOST=http://localhost/audiobookshelf
AUDIOBOOKSHELF_USERNAME=your_username
AUDIOBOOKSHELF_PASSWORD=your_password
```

## Reference

- API documentation: https://api.audiobookshelf.org/
- Code Snippets: `scripts/`

## Python API Packages

- [aioaudiobookshelf](https://pypi.org/project/aioaudiobookshelf/): Async Python library for Audiobookshelf

## Available Scripts

| Script | Purpose |
|--------|---------|
| `api_client.py` | Common client setup patterns (async and sync) |
| `list_libraries.py` | List all libraries from the server |
| `get_library_items.py` | Get books with filtering by author/series |
| `search_authors.py` | Search and manage authors |
| `update_book_metadata.py` | Update book metadata via PATCH API |
| `scan_libraries.py` | Trigger library rescans |
| `update_audio_metadata.py` | Update local audio file metadata using mutagen |
| `scan_audiobook_directory.py` | Scan local directories for audiobook info |

## Key Patterns

### Async API with aioaudiobookshelf

```python
from aioaudiobookshelf import SessionConfiguration, get_admin_client_by_token

async with aiohttp.ClientSession() as session:
    session_config = SessionConfiguration(session=session, url=SERVER_URL, token=API_KEY)
    abs_client = await get_admin_client_by_token(session_config=session_config)
    libraries = await abs_client.get_all_libraries()
```

### Sync API with requests

```python
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
response = requests.patch(url, headers=headers, json=payload, timeout=10)
```

### Local Audio Metadata with mutagen

```python
from mutagen.mp4 import MP4
audio = MP4(file_path)
audio.tags['\xa9ART'] = [author]
audio.save()
```

## Instructions

- Review code snippets in `scripts/` for reusable patterns before creating new scripts
- Use `api_client.py` as starting point for new API scripts
- Use `update_audio_metadata.py` patterns for local file metadata updates
- Put generated scripts under `$WORKSPACE_PATH/temp/`
