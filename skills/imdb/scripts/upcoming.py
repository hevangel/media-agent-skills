"""
Get upcoming movies from IMDB via GraphQL API.
"""

import argparse
import json

try:
    from imdb_client import graphql_upcoming
except ImportError:
    from .imdb_client import graphql_upcoming


def upcoming(limit=20):
    """Get list of upcoming movies."""
    print(f"Fetching upcoming movies (limit={limit})...")
    data = graphql_upcoming(limit=limit)
    print(f"Found {data['result_count']} upcoming titles, showing {len(data['results'])}.")
    return data


def display_results(data):
    """Pretty print upcoming movies."""
    for i, item in enumerate(data.get("results", []), 1):
        name = item.get("name", "Unknown")
        release = item.get("releaseDate", "TBD")
        rating = item.get("rating")
        rating_str = f" - {rating}/10" if rating else ""
        print(f"  [{i}] {name} - {release}{rating_str}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get upcoming movies from IMDB")
    parser.add_argument("--limit", type=int, default=20, help="Number of results")
    args = parser.parse_args()

    data = upcoming(limit=args.limit)
    display_results(data)
