---
name: qbittorrent
description: "Control qBittorrent via the qbittorrent-api Python package. List, add, pause, resume, and delete torrents. Use when managing torrent downloads."
license: MIT
compatibility: Requires Python 3.13+, uv, and qbittorrent-api
---

# qBittorrent Client

## Configuration

All settings are loaded from the `.env` file in the workspace root.

```env
QBITTORRENT_HOST=http://localhost:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=your_password
```

## Reference

- qBittorrent API: https://qbittorrent-api.readthedocs.io/
- Code Snippets: `scripts/`

## Python Package

- [qbittorrent-api](https://pypi.org/project/qbittorrent-api/): Python client for qBittorrent Web API

## Available Functions (`scripts/qbittorrent_client.py`)

| Function | Description |
|----------|-------------|
| `get_client()` | Create and authenticate a qBittorrent client |
| `list_torrents(client)` | List all torrents with status info |
| `add_magnet(client, magnet_link, save_path)` | Add a torrent via magnet link |
| `resume_torrent(client, torrent_hash)` | Resume/start a torrent |
| `pause_torrent(client, torrent_hash)` | Pause a torrent |
| `delete_torrent(client, torrent_hash, delete_files)` | Delete a torrent |
| `get_torrent_by_hash(client, torrent_hash)` | Get a specific torrent by hash |

## Usage

```python
from skills.qbittorrent.scripts.qbittorrent_client import (
    get_client, list_torrents, add_magnet, resume_torrent,
)

client = get_client()

# List all torrents
for torrent in list_torrents(client):
    print(f"{torrent['name']}: {torrent['progress']:.1f}%")

# Add a magnet link
add_magnet(client, "magnet:?xt=urn:btih:...")

# Resume a torrent
resume_torrent(client, "torrent_hash_here")
```

## Notes

- Temporary files go in `$WORKSPACE_PATH/temp/`.
- Avoid `python -c`; create temp scripts instead.
