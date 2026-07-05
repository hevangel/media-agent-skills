---
name: imdb
description: "Search IMDB for movies, TV series, and people. Get details by name or ID, browse upcoming/popular titles. Use when looking up movie/TV/celebrity info from IMDB."
license: MIT
compatibility: Requires Python 3.13+, uv, and requests
---

# IMDB Lookup

Search and retrieve movie, TV series, and celebrity information from IMDB using
IMDB's public Suggestion API (search) and GraphQL API (details).

No API key, scraping, or browser rendering required.

## Reference

- Code Snippets: `scripts/`
- IMDB Suggestion API: `v3.sg.media-imdb.com/suggestion/`
- IMDB GraphQL API: `graphql.imdb.com`

## Available Scripts

| Script | Purpose |
|--------|---------|
| `imdb_client.py` | Core client: suggestion API (search) + GraphQL API (details) |
| `search.py` | Search IMDB by title, year, TV, or person |
| `get_by_name.py` | Get movie/TV series info by name |
| `get_by_id.py` | Get movie/TV series info by IMDB ID |
| `person.py` | Get celebrity profile by name or IMDB ID |
| `upcoming.py` | List upcoming movies (optionally by region) |
| `popular.py` | List popular movies or TV series by genre |

## How It Works

1. **Suggestion API** (`v3.sg.media-imdb.com/suggestion/`) — fast autocomplete search by name
2. **GraphQL API** (`graphql.imdb.com`) — full title details, person profiles, popular/upcoming listings

Only `requests` is needed as a dependency. No browser, proxy, or API key required.

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | String | Movie/TV series/person name |
| `year` | Integer | Filter search results by year |
| `tv` | Boolean | Restrict to TV series only |
| `person` | Boolean | Search for people instead of titles |
| `genre` | String | Genre filter for popular listings (title-cased internally) |

## Usage

### Search for a Movie or TV Series

```python
from imdb_client import suggest_search

results = suggest_search("Inception")
for r in results:
    print(f"{r['name']} ({r['year']}) - {r['id']}")
```

### Get Movie Details by Name

```python
from imdb_client import suggest_search, graphql_get_title

results = suggest_search("Inception")
title_id = results[0]["id"]
info = graphql_get_title(title_id)
print(info)  # dict with type, name, poster, rating, genre, actors, director, etc.
```

### Get by IMDB ID

```python
from imdb_client import graphql_get_title

info = graphql_get_title("tt1375666")
print(info)
```

### Get TV Series Info

```python
from imdb_client import suggest_search, graphql_get_title

results = suggest_search("Reacher")
tv_results = [r for r in results if r["type"] in ("tvSeries", "tvMiniSeries")]
info = graphql_get_title(tv_results[0]["id"])
print(info)
```

### Get Celebrity Profile

```python
from imdb_client import suggest_search, graphql_get_person

results = suggest_search("Brad Pitt")
person_results = [r for r in results if r["id"].startswith("nm")]
profile = graphql_get_person(person_results[0]["id"])
# or directly by ID: graphql_get_person("nm0000093")
print(profile)
```

### Upcoming Movies

```python
from imdb_client import graphql_upcoming

upcoming = graphql_upcoming(limit=20)
for movie in upcoming["results"]:
    print(f"{movie['name']} - {movie['releaseDate']}")
```

### Popular Movies/TV by Genre

```python
from imdb_client import graphql_popular

movies = graphql_popular(title_type="movie", genre="sci-fi", limit=20)
tv = graphql_popular(title_type="tv", genre="action", limit=20)
```

## Response Fields (Movie/TV)

| Field | Description |
|-------|-------------|
| `type` | "Movie" or "TVSeries" |
| `name` | Title |
| `url` | IMDB URL |
| `poster` | Poster image URL |
| `description` | Plot summary |
| `rating` | Object with `ratingValue`, `ratingCount`, `bestRating`, `worstRating` |
| `contentRating` | Age rating |
| `genre` | List of genres |
| `datePublished` | Release date |
| `keywords` | Comma-separated keywords |
| `duration` | ISO 8601 duration |
| `actor` | List of `{name, url}` |
| `director` | List of `{name, url}` |
| `creator` | List of `{name, url}` (writers) |

## Response Fields (Person)

| Field | Description |
|-------|-------------|
| `name` | Full name |
| `url` | IMDB profile URL |
| `image` | Profile image URL |
| `jobTitle` | Primary profession |
| `description` | Bio summary |
| `birthDate` | Date of birth |
| `type` | "Person" |

## Genres (for popular listings)

action, adventure, animation, biography, comedy, crime, documentary, drama, family, fantasy, history, horror, music, mystery, romance, sci-fi, sport, thriller, war, western

## CLI Usage

```bash
cd skills/imdb/scripts
uv run python search.py "Inception" --year 2010
uv run python get_by_name.py "Inception"
uv run python get_by_name.py "Reacher" --tv
uv run python get_by_id.py tt1375666
uv run python person.py "Brad Pitt"
uv run python person.py --id nm0000093
uv run python upcoming.py --limit 20
uv run python popular.py movies --genre sci-fi
uv run python popular.py tv --genre action
```
