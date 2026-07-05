"""
Get TV series details from TheTVDB by ID.
"""

import argparse
import json
import sys

try:
    from tvdb_client import get_client
except ImportError:
    from .tvdb_client import get_client


def get_series(series_id, extended=False):
    """Look up a TV series by TVDB ID."""
    print(f"Looking up TVDB series ID {series_id} (extended={extended})...")
    tvdb = get_client()
    if extended:
        data = tvdb.get_series_extended(series_id)
    else:
        data = tvdb.get_series(series_id)
    if data:
        print(f"Found: {data.get('name')}")
        return data
    print("Not found.")
    return {}


def display_info(data, extended=False):
    """Pretty print series info."""
    print(f"\n  Name:        {data.get('name', 'N/A')}")
    print(f"  TVDB ID:     {data.get('id', 'N/A')}")
    print(f"  Status:      {data.get('status', {}).get('name', 'N/A') if isinstance(data.get('status'), dict) else data.get('status', 'N/A')}")
    print(f"  First Aired: {data.get('firstAired', 'N/A')}")
    print(f"  Last Aired:  {data.get('lastAired', 'N/A')}")
    print(f"  Next Aired:  {data.get('nextAired', 'N/A')}")
    print(f"  Network:     {data.get('originalNetwork', {}).get('name', 'N/A') if isinstance(data.get('originalNetwork'), dict) else 'N/A'}")
    print(f"  Country:     {data.get('originalCountry', 'N/A')}")
    print(f"  Language:    {data.get('originalLanguage', 'N/A')}")
    print(f"  Score:       {data.get('score', 'N/A')}")
    print(f"  URL:         https://thetvdb.com/series/{data.get('slug', '')}")

    overview = data.get("overview", "")
    if overview:
        print(f"  Overview:    {overview[:200]}{'...' if len(overview) > 200 else ''}")

    genres = data.get("genres", [])
    if genres:
        genre_names = [g.get("name", g) if isinstance(g, dict) else str(g) for g in genres]
        print(f"  Genres:      {', '.join(genre_names)}")

    if extended:
        seasons = data.get("seasons", [])
        if seasons:
            aired = [s for s in seasons if s.get("type", {}).get("name") == "Aired Order"]
            print(f"\n  Seasons ({len(aired)} aired):")
            for s in sorted(aired, key=lambda x: x.get("number", 0)):
                print(f"    Season {s['number']}: ID {s['id']}")

        characters = data.get("characters", [])
        if characters:
            print(f"\n  Characters ({len(characters)}):")
            for c in characters[:10]:
                person = c.get("personName", "Unknown")
                role = c.get("name", "Unknown")
                print(f"    {person} as {role}")
            if len(characters) > 10:
                print(f"    ... and {len(characters) - 10} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get TV series info from TheTVDB")
    parser.add_argument("id", type=int, help="TVDB series ID")
    parser.add_argument("--extended", action="store_true", help="Get extended info with seasons and characters")
    args = parser.parse_args()

    data = get_series(args.id, extended=args.extended)
    display_info(data, extended=args.extended)
