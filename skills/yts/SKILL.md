---
name: yts
description: "Search and download movie torrents from YTS (YIFY releases). Use when the user needs to find or download movie torrents with quality and rating filters."
license: MIT
compatibility: Requires Python 3.13+, uv, and pyYify
---

# YTS Movie Torrents

YTS is a popular movie torrent site known for high-quality releases with small file sizes. All movies include multiple quality options (720p, 1080p, 2160p/4K).

**Site:** [https://ytz.mx/](https://ytz.mx/) — API calls try this host first, then common mirrors (`yts.lt`, `yts.mx`) unless you set **`YTS_API_BASE`** (no trailing slash; include `/api/v2`).

## Reference

- Code Snippets: `scripts/`
- YTS API: `search_movies.py` tries `ytz.mx`, then `yts.lt`, then `yts.mx`, or set **`YTS_API_BASE`**
- qBittorrent Integration: See the `qbittorrent` skill

## Python Package

- [pyYify](https://pypi.org/project/pyYify/): Python library for the YTS JSON API (package name is historical; it works with YTS-compatible endpoints)

## Available Scripts

| Script | Purpose |
|--------|---------|
| `search_movies.py` | Search for movies by title, genre, rating |
| `download_movie.py` | Add movie torrent to qBittorrent |

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `quality` | String | 480p, 720p, 1080p, 2160p, 3D |
| `minimum_rating` | Integer (0-9) | Minimum IMDb rating |
| `query_term` | String | Title, IMDb code, actor/director |
| `genre` | String | action, comedy, drama, sci-fi, etc. |
| `sort_by` | String | title, year, rating, seeds, date_added |

## Usage

```python
from pyYify import yify

movies = yify.search_movies("Inception", quality="1080p", minimum_rating=7)
for movie in movies:
    print(f"{movie.title} ({movie.year}) - IMDb: {movie.rating}")
    for torrent in movie.torrents:
        print(f"  {torrent.quality}: {torrent.size} - Seeds: {torrent.seeds}")
```

## Direct API Access

```python
import os
import requests

base = os.environ.get("YTS_API_BASE")  # e.g. https://ytz.mx/api/v2
if not base:
    for candidate in ("https://ytz.mx/api/v2", "https://yts.lt/api/v2", "https://yts.mx/api/v2"):
        try:
            r = requests.get(f"{candidate}/list_movies.json", params={"limit": 1}, timeout=15)
            r.json()
            base = candidate
            break
        except Exception:
            continue
if not base:
    base = "https://ytz.mx/api/v2"
url = f"{base}/list_movies.json"
params = {"query_term": "Inception", "quality": "1080p", "sort_by": "seeds", "limit": 10}
response = requests.get(url, params=params)
data = response.json()
```

## Integration with qBittorrent

```python
from pyYify import yify
from skills.qbittorrent.scripts.qbittorrent_client import get_client, add_magnet

movies = yify.search_movies("Dune", quality="1080p")
if movies:
    torrent = next((t for t in movies[0].torrents if t.quality == "1080p"), movies[0].torrents[0])
    client = get_client()
    add_magnet(client, torrent.magnet)
```

## Genres

action, adventure, animation, biography, comedy, crime, documentary, drama, family, fantasy, history, horror, music, mystery, romance, sci-fi, sport, thriller, war, western
