---
name: tvdb
description: "Search and retrieve TV series, movie, and people info from TheTVDB. Get details by ID, list episodes, seasons, and artwork. Use when looking up TV/movie metadata from TheTVDB."
license: MIT
compatibility: Requires Python 3.13+, uv, and tvdb_v4_official
---

# TheTVDB Lookup

Search and retrieve TV series, movie, episode, and people information from
TheTVDB using the official `tvdb_v4_official` Python package (TVDB API v4).

## Environment Variables

```env
TVDB_API_KEY=your-api-key-here
```

## Reference

- Code Snippets: `scripts/`
- Official Python package: `tvdb_v4_official` ([GitHub](https://github.com/thetvdb/tvdb-v4-python))
- API docs: https://thetvdb.github.io/v4-api/

## Available Scripts

| Script | Purpose |
|--------|---------|
| `tvdb_client.py` | Core client: wraps `tvdb_v4_official` with env-based auth |
| `search.py` | Search TVDB by query (series, movies, people) |
| `get_series.py` | Get TV series info by TVDB ID |
| `get_movie.py` | Get movie info by TVDB ID |
| `get_episodes.py` | List episodes for a series |
| `get_person.py` | Get person info by TVDB ID |

## How It Works

1. Authenticates using `TVDB_API_KEY` from `.env` via the `tvdb_v4_official.TVDB` client
2. The client obtains a bearer token automatically (valid for 1 month)
3. All methods return Python dicts parsed from TVDB API JSON responses

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | String | Search term (series name, movie title, person) |
| `type` | String | Filter: `series`, `movie`, `person` |
| `year` | Integer | Filter by year |
| `limit` | Integer | Max results to return |

## Usage

### Search for a Series or Movie

```python
from tvdb_client import get_client

tvdb = get_client()
results = tvdb.search("Breaking Bad", type="series")
for r in results:
    print(f"{r['name']} ({r.get('year', 'N/A')}) - ID: {r.get('tvdb_id')}")
```

### Get Series Details by ID

```python
from tvdb_client import get_client

tvdb = get_client()
series = tvdb.get_series(81189)  # Breaking Bad
print(series["name"], series.get("year"))
```

### Get Extended Series Info (with seasons, characters, etc.)

```python
from tvdb_client import get_client

tvdb = get_client()
series = tvdb.get_series_extended(81189)
for season in series.get("seasons", []):
    print(f"Season {season['number']} ({season['type']['name']})")
```

### List Episodes for a Series

```python
from tvdb_client import get_client

tvdb = get_client()
info = tvdb.get_series_episodes(81189, season_type="default", page=0)
for ep in info["episodes"]:
    print(f"S{ep['seasonNumber']:02d}E{ep['number']:02d} - {ep['name']}")
```

### Get Movie Details

```python
from tvdb_client import get_client

tvdb = get_client()
movie = tvdb.get_movie(31)  # Avengers
print(movie["name"])

# Extended info with characters
movie_ext = tvdb.get_movie_extended(31)
for c in movie_ext.get("characters", []):
    print(f"  {c.get('name')} - {c.get('personName')}")
```

### Get Person Info

```python
from tvdb_client import get_client

tvdb = get_client()
person = tvdb.get_person_extended(253463)
print(person["name"])
```

### Get Next Airing for a Series

```python
from tvdb_client import get_client

tvdb = get_client()
next_aired = tvdb.get_series_nextAired(81189)
print(next_aired)
```

## Key API Methods

| Method | Description |
|--------|-------------|
| `search(query, **kwargs)` | Search across series, movies, people |
| `get_series(id)` | Basic series record |
| `get_series_extended(id)` | Full series with seasons, characters, artwork |
| `get_series_episodes(id, season_type, page)` | Paginated episode list |
| `get_series_nextAired(id)` | Next airing episode |
| `get_series_artworks(id, lang)` | Series artwork |
| `get_movie(id)` | Basic movie record |
| `get_movie_extended(id)` | Full movie with characters, artwork |
| `get_episode(id)` | Basic episode record |
| `get_episode_extended(id)` | Full episode details |
| `get_season(id)` | Basic season record |
| `get_season_extended(id)` | Full season with episodes |
| `get_person(id)` | Basic person record |
| `get_person_extended(id)` | Full person with roles |
| `get_all_genres()` | List all genres |

## CLI Usage

```bash
cd skills/tvdb/scripts
uv run python search.py "Breaking Bad"
uv run python search.py "Breaking Bad" --type series
uv run python search.py "Avengers" --type movie --year 2012
uv run python get_series.py 81189
uv run python get_series.py 81189 --extended
uv run python get_movie.py 31
uv run python get_movie.py 31 --extended
uv run python get_episodes.py 81189
uv run python get_episodes.py 81189 --season 1
uv run python get_person.py 253463
```
