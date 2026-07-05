"""
Get movie or TV series details from IMDB by name.
Uses IMDB suggestion API to find the title, then GraphQL for details.
"""

import argparse
import json
import sys

try:
    from imdb_client import suggest_search, graphql_get_title
except ImportError:
    from .imdb_client import suggest_search, graphql_get_title


def get_by_name(name, tv=False):
    """Look up a movie or TV series by name and return parsed info."""
    label = "TV series" if tv else "movie/TV"
    print(f"Looking up {label} '{name}' on IMDB...")

    results = suggest_search(name)
    if tv:
        results = [r for r in results if r.get("type") in ("tvSeries", "tvMiniSeries")]
    else:
        results = [r for r in results if r.get("id", "").startswith("tt")]

    if not results:
        print("No results found.")
        return {}

    imdb_id = results[0]["id"]
    print(f"Found match: {results[0]['name']} ({imdb_id}), fetching details...")
    data = graphql_get_title(imdb_id)
    if data:
        print(f"Found: {data.get('name')} ({data.get('type', 'Unknown')})")
        return data

    print("Could not retrieve details.")
    return {}


def display_info(data):
    """Pretty print movie/TV info."""
    print(f"\n  Title:    {data.get('name', 'N/A')}")
    print(f"  Type:     {data.get('type', 'N/A')}")
    print(f"  URL:      {data.get('url', 'N/A')}")

    rating = data.get("rating", {})
    if rating:
        print(f"  Rating:   {rating.get('ratingValue', 'N/A')}/10 ({rating.get('ratingCount', 0)} votes)")

    print(f"  Genre:    {', '.join(data.get('genre', []))}")
    print(f"  Released: {data.get('datePublished', 'N/A')}")
    print(f"  Duration: {data.get('duration', 'N/A')}")

    actors = data.get("actor", [])
    if actors:
        names = [a.get("name", "") for a in actors[:5]]
        print(f"  Cast:     {', '.join(names)}")

    directors = data.get("director", [])
    if directors:
        names = [d.get("name", "") for d in directors]
        print(f"  Director: {', '.join(names)}")

    desc = data.get("description", "")
    if desc:
        print(f"  Plot:     {desc[:200]}{'...' if len(desc) > 200 else ''}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get movie/TV info from IMDB by name")
    parser.add_argument("name", help="Movie or TV series name")
    parser.add_argument("--tv", action="store_true", help="Search TV series only")
    args = parser.parse_args()

    data = get_by_name(args.name, tv=args.tv)
    display_info(data)
