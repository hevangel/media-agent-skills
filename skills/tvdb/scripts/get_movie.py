"""
Get movie details from TheTVDB by ID.
"""

import argparse
import json
import sys

try:
    from tvdb_client import get_client
except ImportError:
    from .tvdb_client import get_client


def get_movie(movie_id, extended=False):
    """Look up a movie by TVDB ID."""
    print(f"Looking up TVDB movie ID {movie_id} (extended={extended})...")
    tvdb = get_client()
    if extended:
        data = tvdb.get_movie_extended(movie_id)
    else:
        data = tvdb.get_movie(movie_id)
    if data:
        print(f"Found: {data.get('name')}")
        return data
    print("Not found.")
    return {}


def display_info(data, extended=False):
    """Pretty print movie info."""
    print(f"\n  Name:        {data.get('name', 'N/A')}")
    print(f"  TVDB ID:     {data.get('id', 'N/A')}")
    print(f"  Year:        {data.get('year', 'N/A')}")
    print(f"  Runtime:     {data.get('runtime', 'N/A')} min")
    print(f"  Score:       {data.get('score', 'N/A')}")
    print(f"  URL:         https://thetvdb.com/movies/{data.get('slug', '')}")

    overview = data.get("overview", "")
    if overview:
        print(f"  Overview:    {overview[:200]}{'...' if len(overview) > 200 else ''}")

    genres = data.get("genres", [])
    if genres:
        genre_names = [g.get("name", g) if isinstance(g, dict) else str(g) for g in genres]
        print(f"  Genres:      {', '.join(genre_names)}")

    if extended:
        characters = data.get("characters", [])
        if characters:
            print(f"\n  Characters ({len(characters)}):")
            for c in characters[:10]:
                person = c.get("personName", "Unknown")
                role = c.get("name", "Unknown")
                print(f"    {person} as {role}")
            if len(characters) > 10:
                print(f"    ... and {len(characters) - 10} more")

        trailers = data.get("trailers", [])
        if trailers:
            print(f"\n  Trailers ({len(trailers)}):")
            for t in trailers[:5]:
                print(f"    {t.get('name', 'N/A')}: {t.get('url', 'N/A')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get movie info from TheTVDB")
    parser.add_argument("id", type=int, help="TVDB movie ID")
    parser.add_argument("--extended", action="store_true", help="Get extended info with characters and trailers")
    args = parser.parse_args()

    data = get_movie(args.id, extended=args.extended)
    display_info(data, extended=args.extended)
