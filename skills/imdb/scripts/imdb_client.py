"""
IMDB API client using IMDB's public Suggestion and GraphQL APIs.

- Suggestion API: fast autocomplete search
- GraphQL API: full title/person details, popular/upcoming listings

No scraping or browser rendering required.
"""

import json
from datetime import date

import requests


GRAPHQL_URL = "https://graphql.imdb.com/"
SUGGEST_URL = "https://v3.sg.media-imdb.com/suggestion/x/{query}.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

# Genre IDs must be title-cased for GraphQL
GENRE_MAP = {
    "action": "Action", "adventure": "Adventure", "animation": "Animation",
    "biography": "Biography", "comedy": "Comedy", "crime": "Crime",
    "documentary": "Documentary", "drama": "Drama", "family": "Family",
    "fantasy": "Fantasy", "history": "History", "horror": "Horror",
    "music": "Music", "mystery": "Mystery", "romance": "Romance",
    "sci-fi": "Sci-Fi", "sport": "Sport", "thriller": "Thriller",
    "war": "War", "western": "Western",
}

# GraphQL query for movie/TV details
TITLE_QUERY = """
query GetTitle($id: ID!) {
  title(id: $id) {
    titleText { text }
    originalTitleText { text }
    releaseYear { year endYear }
    titleType { text }
    plot { plotText { plainText } }
    ratingsSummary { aggregateRating voteCount }
    primaryImage { url width height }
    genres { genres { text } }
    runtime { seconds displayableProperty { value { plainText } } }
    releaseDate { day month year }
    certificate { rating }
    keywords(first: 10) { edges { node { text } } }
    directors: credits(first: 5, filter: {categories: ["director"]}) {
      edges { node { name { nameText { text } id } } }
    }
    writers: credits(first: 5, filter: {categories: ["writer"]}) {
      edges { node { name { nameText { text } id } } }
    }
    cast: credits(first: 10, filter: {categories: ["actor", "actress"]}) {
      edges { node { name { nameText { text } id } } }
    }
  }
}
"""

# GraphQL query for person details
PERSON_QUERY = """
query GetPerson($id: ID!) {
  name(id: $id) {
    nameText { text }
    primaryImage { url }
    primaryProfessions { category { text } }
    bio { text { plainText } }
    birthDate { dateComponents { day month year } }
    deathDate { dateComponents { day month year } }
    knownFor(first: 5) {
      edges { node { title { titleText { text } id releaseYear { year } } } }
    }
  }
}
"""

# GraphQL query for popular/upcoming title lists - built dynamically
_SEARCH_FIELDS = """
    edges {
      node {
        title {
          id
          titleText { text }
          releaseYear { year }
          releaseDate { day month year }
          titleType { text }
          ratingsSummary { aggregateRating voteCount }
          primaryImage { url }
          genres { genres { text } }
        }
      }
    }
    total
"""


def suggest_search(query, timeout=10):
    """
    Search IMDB using the suggestion/autocomplete API.
    Returns a list of result dicts with id, name, year, type, image, stars.
    """
    encoded = requests.utils.quote(query.lower())
    url = SUGGEST_URL.format(query=encoded)
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("d", []):
        results.append({
            "id": item.get("id", ""),
            "name": item.get("l", ""),
            "year": item.get("y"),
            "type": item.get("qid", ""),
            "url": f"https://www.imdb.com/title/{item['id']}/" if item.get("id", "").startswith("tt") else f"https://www.imdb.com/name/{item['id']}/",
            "poster": item.get("i", {}).get("imageUrl"),
            "stars": item.get("s", ""),
        })
    return results


def graphql_get_title(imdb_id, timeout=10):
    """
    Get full title details via IMDB's GraphQL API.
    Returns a normalized dict matching PyMovieDb's output format.
    """
    r = requests.post(
        GRAPHQL_URL,
        json={"query": TITLE_QUERY, "variables": {"id": imdb_id}},
        headers=HEADERS,
        timeout=timeout,
    )
    r.raise_for_status()
    title = r.json().get("data", {}).get("title")
    if not title:
        return None

    # Normalize to match PyMovieDb output format
    runtime_secs = (title.get("runtime") or {}).get("seconds")
    duration = None
    if runtime_secs:
        hours = runtime_secs // 3600
        mins = (runtime_secs % 3600) // 60
        duration = f"PT{hours}H{mins}M" if hours else f"PT{mins}M"

    release = title.get("releaseDate") or {}
    date_parts = [str(release.get("year", "")), str(release.get("month", "")).zfill(2), str(release.get("day", "")).zfill(2)]
    date_published = "-".join(date_parts) if release.get("year") else None

    content_rating = (title.get("certificate") or {}).get("rating")

    keywords_edges = (title.get("keywords") or {}).get("edges", [])
    keywords = ",".join(e["node"]["text"] for e in keywords_edges if e.get("node"))

    def extract_credits(credit_data):
        edges = (credit_data or {}).get("edges", [])
        return [
            {"name": e["node"]["name"]["nameText"]["text"], "url": f"/name/{e['node']['name']['id']}/"}
            for e in edges if e.get("node")
        ]

    type_text = (title.get("titleType") or {}).get("text", "")
    # Map IMDB type text to PyMovieDb format
    type_map = {"Movie": "Movie", "TV Series": "TVSeries", "TV Mini Series": "TVMiniSeries",
                "Short": "Short", "TV Movie": "TVMovie", "TV Episode": "TVEpisode",
                "TV Special": "TVSpecial", "Video": "Video"}

    rating_summary = title.get("ratingsSummary") or {}

    return {
        "type": type_map.get(type_text, type_text),
        "name": (title.get("titleText") or {}).get("text"),
        "url": f"https://www.imdb.com/title/{imdb_id}/",
        "poster": (title.get("primaryImage") or {}).get("url"),
        "description": ((title.get("plot") or {}).get("plotText") or {}).get("plainText"),
        "rating": {
            "ratingCount": rating_summary.get("voteCount"),
            "bestRating": 10,
            "worstRating": 1,
            "ratingValue": rating_summary.get("aggregateRating"),
        },
        "contentRating": content_rating,
        "genre": [g["text"] for g in (title.get("genres") or {}).get("genres", [])],
        "datePublished": date_published,
        "keywords": keywords,
        "duration": duration,
        "actor": extract_credits(title.get("cast")),
        "director": extract_credits(title.get("directors")),
        "creator": extract_credits(title.get("writers")),
    }


def graphql_get_person(imdb_id, timeout=10):
    """
    Get person details via IMDB's GraphQL API.
    Returns a normalized dict matching PyMovieDb's output format.
    """
    r = requests.post(
        GRAPHQL_URL,
        json={"query": PERSON_QUERY, "variables": {"id": imdb_id}},
        headers=HEADERS,
        timeout=timeout,
    )
    r.raise_for_status()
    name_data = r.json().get("data", {}).get("name")
    if not name_data:
        return None

    birth = name_data.get("birthDate") or {}
    birth_comp = birth.get("dateComponents") or {}
    birth_date = None
    if birth_comp.get("year"):
        parts = [str(birth_comp["year"]), str(birth_comp.get("month", 1)).zfill(2), str(birth_comp.get("day", 1)).zfill(2)]
        birth_date = "-".join(parts)

    professions = name_data.get("primaryProfessions") or []
    job_title = professions[0]["category"]["text"] if professions else None

    bio_text = ((name_data.get("bio") or {}).get("text") or {}).get("plainText", "")

    return {
        "url": f"/name/{imdb_id}/",
        "name": (name_data.get("nameText") or {}).get("text"),
        "image": (name_data.get("primaryImage") or {}).get("url"),
        "jobTitle": job_title,
        "description": bio_text[:500] if bio_text else None,
        "birthDate": birth_date,
        "type": "Person",
    }


def _normalize_genre(genre):
    """Convert genre string to title-cased ID for GraphQL."""
    if not genre:
        return None
    return GENRE_MAP.get(genre.lower(), genre.title())


def _extract_search_titles(data):
    """Extract title list from advancedTitleSearch response."""
    edges = data.get("data", {}).get("advancedTitleSearch", {}).get("edges", [])
    total = data.get("data", {}).get("advancedTitleSearch", {}).get("total", 0)
    results = []
    for e in edges:
        t = e.get("node", {}).get("title", {})
        rd = t.get("releaseDate") or {}
        date_str = None
        if rd.get("year"):
            date_str = f"{rd['year']}-{str(rd.get('month', 1)).zfill(2)}-{str(rd.get('day', 1)).zfill(2)}"
        results.append({
            "id": t.get("id"),
            "name": (t.get("titleText") or {}).get("text"),
            "year": (t.get("releaseYear") or {}).get("year"),
            "type": (t.get("titleType") or {}).get("text"),
            "url": f"https://www.imdb.com/title/{t.get('id')}/" if t.get("id") else None,
            "poster": (t.get("primaryImage") or {}).get("url"),
            "rating": (t.get("ratingsSummary") or {}).get("aggregateRating"),
            "votes": (t.get("ratingsSummary") or {}).get("voteCount"),
            "genre": [g["text"] for g in (t.get("genres") or {}).get("genres", [])],
            "releaseDate": date_str,
        })
    return {"result_count": total, "results": results}


def _run_advanced_search(title_types, genres=None, start_date=None,
                         sort_by="POPULARITY", sort_order="ASC", limit=20, timeout=10):
    """Run an advancedTitleSearch query and return normalized results."""
    constraints = [f'titleTypeConstraint: {{anyTitleTypeIds: {json.dumps(title_types)}}}']
    if genres:
        constraints.append(f'genreConstraint: {{allGenreIds: {json.dumps(genres)}}}')
    if start_date:
        constraints.append(f'releaseDateConstraint: {{releaseDateRange: {{start: "{start_date}"}}}}')
    constraints_str = ", ".join(constraints)

    query = f"""
query {{
  advancedTitleSearch(
    first: {limit},
    sort: {{sortBy: {sort_by}, sortOrder: {sort_order}}},
    constraints: {{{constraints_str}}}
  ) {{{_SEARCH_FIELDS}}}
}}
"""
    r = requests.post(GRAPHQL_URL, json={"query": query}, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return _extract_search_titles(r.json())


def graphql_upcoming(limit=20, timeout=10):
    """Get upcoming movies via GraphQL advancedTitleSearch."""
    today = date.today().isoformat()
    return _run_advanced_search(
        title_types=["movie"],
        start_date=today,
        sort_by="RELEASE_DATE",
        sort_order="ASC",
        limit=limit,
        timeout=timeout,
    )


def graphql_popular(title_type="movie", genre=None, limit=20, timeout=10):
    """Get popular movies or TV series via GraphQL advancedTitleSearch."""
    title_types = ["tvSeries", "tvMiniSeries"] if title_type == "tv" else ["movie"]
    genre_id = _normalize_genre(genre)
    genres = [genre_id] if genre_id else None
    return _run_advanced_search(
        title_types=title_types,
        genres=genres,
        sort_by="POPULARITY",
        sort_order="ASC",
        limit=limit,
        timeout=timeout,
    )
