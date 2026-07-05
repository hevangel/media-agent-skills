"""
Get popular movies or TV series from IMDB via GraphQL API.
"""

import argparse
import json

try:
    from imdb_client import graphql_popular
except ImportError:
    from .imdb_client import graphql_popular


def popular_movies(genre=None, limit=20):
    """Get popular movies, optionally filtered by genre."""
    print(f"Fetching popular movies (genre={genre}, limit={limit})...")
    data = graphql_popular(title_type="movie", genre=genre, limit=limit)
    print(f"Found {data['result_count']} titles, showing {len(data['results'])}.")
    return data


def popular_tv(genre=None, limit=20):
    """Get popular TV series, optionally filtered by genre."""
    print(f"Fetching popular TV series (genre={genre}, limit={limit})...")
    data = graphql_popular(title_type="tv", genre=genre, limit=limit)
    print(f"Found {data['result_count']} titles, showing {len(data['results'])}.")
    return data


def display_results(data):
    """Pretty print popular titles."""
    for i, item in enumerate(data.get("results", []), 1):
        name = item.get("name", "Unknown")
        year = item.get("year", "")
        rating = item.get("rating")
        genre = ", ".join(item.get("genre", []))
        year_str = f" ({year})" if year else ""
        rating_str = f" - {rating}/10" if rating else ""
        genre_str = f" [{genre}]" if genre else ""
        print(f"  [{i}] {name}{year_str}{rating_str}{genre_str}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get popular movies/TV from IMDB")
    parser.add_argument("type", choices=["movies", "tv"], help="Content type")
    parser.add_argument("--genre", help="Genre filter (e.g. sci-fi, action, comedy)")
    parser.add_argument("--limit", type=int, default=20, help="Number of results")
    args = parser.parse_args()

    if args.type == "movies":
        data = popular_movies(genre=args.genre, limit=args.limit)
    else:
        data = popular_tv(genre=args.genre, limit=args.limit)

    display_results(data)
