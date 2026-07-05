"""
Search IMDB for movies, TV series, or people.
Uses IMDB's suggestion/autocomplete API.
"""

import argparse
import json
import sys

try:
    from imdb_client import suggest_search
except ImportError:
    from .imdb_client import suggest_search


def search(query, year=None, tv=False, person=False):
    """Search IMDB and return parsed results."""
    print(f"Searching IMDB for '{query}' (year={year}, tv={tv}, person={person})...")
    results = suggest_search(query)

    # Filter by type
    if tv:
        results = [r for r in results if r.get("type") in ("tvSeries", "tvMiniSeries")]
    elif person:
        results = [r for r in results if r.get("id", "").startswith("nm")]
    else:
        results = [r for r in results if r.get("id", "").startswith("tt") or r.get("id", "").startswith("nm")]

    # Filter by year
    if year:
        results = [r for r in results if r.get("year") == year]

    data = {"result_count": len(results), "results": results}
    print(f"Found {data['result_count']} result(s).")
    return data


def display_results(data):
    """Pretty print search results."""
    results = data.get("results", [])
    for i, item in enumerate(results, 1):
        name = item.get("name", "Unknown")
        imdb_id = item.get("id", "N/A")
        year = item.get("year", "")
        stars = item.get("stars", "")
        year_str = f" ({year})" if year else ""
        print(f"  [{i}] {name}{year_str} - ID: {imdb_id}")
        if stars:
            print(f"       Stars: {stars}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search IMDB")
    parser.add_argument("query", help="Search term")
    parser.add_argument("--year", type=int, help="Filter by year")
    parser.add_argument("--tv", action="store_true", help="Search TV series only")
    parser.add_argument("--person", action="store_true", help="Search people only")
    args = parser.parse_args()

    data = search(args.query, year=args.year, tv=args.tv, person=args.person)
    display_results(data)
