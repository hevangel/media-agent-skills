"""
Search TheTVDB for series, movies, or people.
"""

import argparse
import json
import sys

try:
    from tvdb_client import get_client
except ImportError:
    from .tvdb_client import get_client


def search(query, type=None, year=None, limit=25):
    """Search TVDB and return results."""
    print(f"Searching TVDB for '{query}' (type={type}, year={year})...")
    tvdb = get_client()
    kwargs = {}
    if type:
        kwargs["type"] = type
    if year:
        kwargs["year"] = str(year)
    if limit:
        kwargs["limit"] = str(limit)
    results = tvdb.search(query, **kwargs)

    data = {"result_count": len(results), "results": results}
    print(f"Found {data['result_count']} result(s).")
    return data


def display_results(data):
    """Pretty print search results."""
    results = data.get("results", [])
    for i, item in enumerate(results, 1):
        name = item.get("name", "Unknown")
        tvdb_id = item.get("tvdb_id", item.get("id", "N/A"))
        item_type = item.get("type", "")
        year = item.get("year", "")
        year_str = f" ({year})" if year else ""
        type_str = f" [{item_type}]" if item_type else ""
        overview = item.get("overview", "") or ""
        overview_str = f"\n       {overview[:120]}..." if len(overview) > 120 else (f"\n       {overview}" if overview else "")
        print(f"  [{i}] {name}{year_str}{type_str} - ID: {tvdb_id}{overview_str}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search TheTVDB")
    parser.add_argument("query", help="Search term")
    parser.add_argument("--type", choices=["series", "movie", "person"], help="Filter by type")
    parser.add_argument("--year", type=int, help="Filter by year")
    parser.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")
    args = parser.parse_args()

    data = search(args.query, type=args.type, year=args.year, limit=args.limit)
    display_results(data)
