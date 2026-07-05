"""
Get movie or TV series details from IMDB by IMDB ID.
Uses IMDB's GraphQL API.
"""

import argparse
import json
import sys

try:
    from imdb_client import graphql_get_title
except ImportError:
    from .imdb_client import graphql_get_title


def get_by_id(imdb_id):
    """Look up a movie or TV series by IMDB ID and return parsed info."""
    print(f"Looking up IMDB ID '{imdb_id}'...")
    data = graphql_get_title(imdb_id)
    if data:
        print(f"Found: {data.get('name')} ({data.get('type', 'Unknown')})")
        return data

    print("Not found.")
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
    parser = argparse.ArgumentParser(description="Get movie/TV info from IMDB by ID")
    parser.add_argument("id", help="IMDB ID (e.g. tt1375666)")
    args = parser.parse_args()

    data = get_by_id(args.id)
    display_info(data)
