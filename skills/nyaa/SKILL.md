---
name: nyaa
description: "Search and download anime torrents from nyaa.si. Use when the user needs to find anime, manga, or East Asian media torrents."
license: MIT
compatibility: Requires Python 3.13+, uv, and nyaapy
---

# Nyaa.si Torrent Search

Nyaa.si is a popular BitTorrent website focused on East Asian media including anime, manga, music, and games.

## Reference

- Code Snippets: `scripts/`
- NyaaPy Documentation: https://github.com/JuanjoSalvador/NyaaPy/wiki
- qBittorrent Integration: See the `qbittorrent` skill

## Python Package

- [nyaapy](https://pypi.org/project/nyaapy/): Unofficial Python wrapper for Nyaa.si

## Categories

| Category | Subcategory | Description |
|----------|-------------|-------------|
| 1 | 0 | Anime (all) |
| 1 | 2 | Anime - English-translated |
| 1 | 3 | Anime - Non-English-translated |
| 1 | 4 | Anime - Raw |
| 2 | 0 | Audio (all) |
| 3 | 0 | Literature (all) |
| 4 | 0 | Live Action (all) |
| 6 | 0 | Software (all) |

## Filters

| Filter | Description |
|--------|-------------|
| 0 | No filter (default) |
| 1 | No remakes |
| 2 | Trusted only |

## Available Scripts

| Script | Purpose |
|--------|---------|
| `search_anime.py` | Search for anime torrents by keyword |
| `download_torrent.py` | Add torrent to qBittorrent via magnet link |

## Usage

```python
from nyaapy.nyaasi.nyaa import Nyaa

# Search English-translated anime
results = Nyaa.search(keyword="Frieren", category=1, subcategory=2)

# Trusted only
results = Nyaa.search(keyword="Frieren", category=1, filters=2)

for r in results[:5]:
    print(f"{r.name} - Size: {r.size} | Seeders: {r.seeders}")
```

## Torrent Properties

`name`, `category`, `url`, `download_url`, `magnet`, `size`, `date`, `seeders`, `leechers`, `completed_downloads`

## Integration with qBittorrent

```python
from nyaapy.nyaasi.nyaa import Nyaa
from skills.qbittorrent.scripts.qbittorrent_client import get_client, add_magnet

results = Nyaa.search(keyword="Frieren", category=1, subcategory=2, filters=2)
if results:
    client = get_client()
    add_magnet(client, results[0].magnet)
```

## Notes

- Temporary files go in `$WORKSPACE_PATH/temp/`.
