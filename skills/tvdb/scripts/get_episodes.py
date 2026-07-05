"""
List episodes for a TV series from TheTVDB.
"""

import argparse
import json
import sys

try:
    from tvdb_client import get_client
except ImportError:
    from .tvdb_client import get_client


def get_episodes(series_id, season=None, season_type="default", page=0):
    """Get episodes for a series, optionally filtered by season number."""
    print(f"Fetching episodes for series {series_id} (season_type={season_type}, page={page})...")
    tvdb = get_client()
    info = tvdb.get_series_episodes(series_id, season_type=season_type, page=page)

    episodes = info.get("episodes", [])
    series_info = info.get("series", {})

    if season is not None:
        episodes = [ep for ep in episodes if ep.get("seasonNumber") == season]

    print(f"Found {len(episodes)} episode(s).")
    return {"series": series_info, "episodes": episodes, "total": len(episodes)}


def display_episodes(data):
    """Pretty print episode list."""
    series = data.get("series", {})
    episodes = data.get("episodes", [])

    if series:
        print(f"\n  Series: {series.get('name', 'N/A')}")

    for ep in episodes:
        s_num = ep.get("seasonNumber", "?")
        e_num = ep.get("number", "?")
        name = ep.get("name", "N/A")
        aired = ep.get("aired", "")
        runtime = ep.get("runtime", "")
        aired_str = f" ({aired})" if aired else ""
        runtime_str = f" [{runtime}min]" if runtime else ""
        print(f"  S{s_num:02d}E{e_num:02d} - {name}{aired_str}{runtime_str}")

    if not episodes:
        print("  No episodes found. Try --page for more pages.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List episodes for a TV series from TheTVDB")
    parser.add_argument("series_id", type=int, help="TVDB series ID")
    parser.add_argument("--season", type=int, help="Filter by season number")
    parser.add_argument("--season-type", default="default", help="Season type (default: 'default')")
    parser.add_argument("--page", type=int, default=0, help="Page number (default: 0)")
    args = parser.parse_args()

    data = get_episodes(args.series_id, season=args.season, season_type=args.season_type, page=args.page)
    display_episodes(data)
