---
name: yify
description: "Search and download movie torrents from YTS/YIFY. Use when the user needs to find or download movie torrents with quality and rating filters."
license: MIT
compatibility: Requires Python 3.13+, uv, and pyYify
---

# YTS/YIFY Movie Torrents

YTS is a popular movie torrent site known for high-quality releases with small file sizes. All movies include multiple quality options (720p, 1080p, 2160p/4K).

## Reference

- Code Snippets: `scripts/`
- YTS API: https://yts.mx/api
- qBittorrent Integration: See the `qbittorrent` skill

## Python Package

- [pyYify](https://pypi.org/project/pyYify/): Python library for YTS API

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
import requests

url = "https://yts.mx/api/v2/list_movies.json"
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
