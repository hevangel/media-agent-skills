---
name: yts
description: "Search and download movie torrents from YTS (YIFY releases). Use when the user needs to find or download movie torrents with quality and rating filters."
license: MIT
compatibility: Requires Python 3.13+, uv, and pyYify
---

# YTS Movie Torrents

YTS is a popular movie torrent site known for high-quality releases with small file sizes. All movies include multiple quality options (720p, 1080p, 2160p/4K).

**Site:** [https://yts.mx/](https://yts.mx/) — API calls try this host first, then the `yts.lt` mirror unless you set **`YTS_API_BASE`** (no trailing slash; include `/api/v2`).

## Reference

- Code Snippets: `scripts/`
- YTS API: `search_movies.py` tries `yts.mx`, then `yts.lt`, or set **`YTS_API_BASE`**
- qBittorrent Integration: See the `qbittorrent` skill

## Python Package

- [pyYify](https://pypi.org/project/pyYify/): Python library for the YTS JSON API (package name is historical; it works with YTS-compatible endpoints)

## Available Scripts

| Script | Purpose |
|--------|---------|
| `search_movies.py` | Search for movies by title, genre, rating |
| `download_movie.py` | Add movie torrent to qBittorrent |
| `movie_selector_server.py` | Serve the movie-selector web app + selection API |
| `download_selected.py` | Add the web-app selected movies' torrents to qBittorrent |
| `movie_selection_store.py` | Selection store module (JSON, shared server <-> script) |

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

base = os.environ.get("YTS_API_BASE")  # e.g. https://yts.mx/api/v2
if not base:
    for candidate in ("https://yts.mx/api/v2", "https://yts.lt/api/v2"):
        try:
            r = requests.get(f"{candidate}/list_movies.json", params={"limit": 1}, timeout=15)
            r.json()
            base = candidate
            break
        except Exception:
            continue
if not base:
    base = "https://yts.mx/api/v2"
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

## Movie Selector Web App

A local web app (`assets/movie_selector/index.html`, served by
`movie_selector_server.py`) for picking movies visually: a table with poster,
screencap, plot summary, IMDb rating, and torrent links per quality.

The browser queries the YTS API directly when it can (the API is
CORS-enabled). When the YTS mirrors are unreachable from the browser's network
(521s, ISP blocks), the page automatically falls back to the backend's
`/api/movies` and `/api/img` endpoints, which fetch through the SSH SOCKS5
tunnel pool (`CTFILE_PROXY_HOSTS` in `.env`, `ssh -D` tunnels via the
tvboxnow `ssh_proxy_pool` module). Proxied requests are restricted to
allowlisted YTS hosts (`yts.mx`, `yts.lt`, `yts.gg`, `movies-api.accel.li`),
with resolved-IP checks against loopback/private/reserved ranges before every
outbound request. Selections persist in
`temp/yts_movie_selector/selection.json` (override with `YTS_SELECTION_PATH`).

```bash
# 1. Start the app (default http://127.0.0.1:8010)
uv run python skills/yts/scripts/movie_selector_server.py
uv run python skills/yts/scripts/movie_selector_server.py --port 8010 --host 127.0.0.1

# 2. Open http://127.0.0.1:8011, search, and click a quality button to queue
#    exactly that torrent (e.g. "＋ 1080p · 1.85 GB"; click ✓ to remove)

# 3. Download everything queued - each entry uses the quality you queued
uv run python skills/yts/scripts/download_selected.py
uv run python skills/yts/scripts/download_selected.py --save-path /path/to/downloads
uv run python skills/yts/scripts/download_selected.py --list        # show queue
uv run python skills/yts/scripts/download_selected.py --dry-run     # print magnets only
```

### Selection API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/selection` | GET | List selection (`?status=pending\|downloaded`) |
| `/api/selection` | POST | Add a movie (JSON body: `{id, title, torrents: [...]}`) |
| `/api/selection/{id}` | DELETE | Remove one movie |
| `/api/selection/clear` | POST | Empty the queue |
| `/api/selection/{id}/status` | POST | Set status `{"status": "pending"\|"downloaded"}` |

Selections keep their status (`pending` -> `downloaded` once handed to
qBittorrent), so re-running `download_selected.py` only processes new picks.
The agent workflow: start the server, let the user pick movies in the browser,
then run `download_selected.py` - no per-movie CLI searching needed.

## Genres

action, adventure, animation, biography, comedy, crime, documentary, drama, family, fantasy, history, horror, music, mystery, romance, sci-fi, sport, thriller, war, western
